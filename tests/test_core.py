import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError
from urllib.request import urlopen

from core import CorruptLibraryError, Library, PreviewManager, github_url


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.library = Library(self.root / 'data' / 'library.json')
        self.site = self.root / 'site'
        self.site.mkdir()
        (self.site / 'index.html').write_text('<h1>Bonjour DevDock</h1>', encoding='utf-8')
        self.manager = PreviewManager()

    def tearDown(self):
        self.manager.stop_all()
        self.temp.cleanup()

    def add(self, **kwargs):
        return self.library.upsert(kwargs.get('name', 'Été'), str(kwargs.get('folder', self.site)), kwargs.get('github', ''))

    def test_save_reload_modify_and_favorite(self):
        p = self.add(github='https://github.com/loghanmrsn/DevDock.git')
        self.library.favorite(p.id)
        self.library.upsert('Nouveau nom', str(self.site), project_id=p.id)
        reloaded = Library(self.library.path)
        reloaded.load()
        self.assertEqual(reloaded.get(p.id).name, 'Nouveau nom')
        self.assertTrue(reloaded.get(p.id).favorite)
        self.assertEqual(reloaded.search(category='favorites'), reloaded.projects)
        reloaded.favorite(p.id)
        self.assertEqual(reloaded.search(category='favorites'), [])

    def test_search_name_path_and_running(self):
        p = self.add()
        self.assertEqual(self.library.search('ÉTÉ'), [p])
        self.assertEqual(self.library.search('SITE'), [p])
        self.assertEqual(self.library.search('inexistant'), [])
        self.assertEqual(self.library.search(category='running'), [])
        self.assertEqual(self.library.search(category='running', running={p.id}), [p])

    def test_invalid_names_paths_duplicates(self):
        self.add()
        for name, folder in [('autre', str(self.site / '..' / 'site')), ('', str(self.root)), ('test', ''), ('test', str(self.root / 'absent'))]:
            with self.subTest(name=name, folder=folder), self.assertRaises(ValueError):
                self.library.upsert(name, folder)

    def test_github_validation(self):
        self.assertEqual(github_url(''), '')
        self.assertEqual(github_url('https://github.com/loghanmrsn/DevDock.git/'), 'https://github.com/loghanmrsn/DevDock')
        for url in ['http://github.com/a/b', 'https://github.com.evil/a/b', 'https://user@github.com/a/b', 'file:///tmp', 'https://github.com/a/b?x=1', 'https://github.com/a/b/issues', 'https://github.com/a/..', 'https://github.com/a/b#x']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                github_url(url)

    def test_atomic_failure_keeps_old_file_and_memory(self):
        p = self.add()
        old = self.library.path.read_bytes()
        with patch('core.os.replace', side_effect=PermissionError('Disque protégé')):
            with self.assertRaises(PermissionError):
                self.library.favorite(p.id)
        self.assertEqual(self.library.path.read_bytes(), old)
        self.assertFalse(self.library.get(p.id).favorite)
        self.assertEqual(list(self.library.path.parent.glob('*.tmp')), [])

    def test_corrupt_file_preserved_and_read_only(self):
        self.library.path.parent.mkdir()
        for payload in [b'{invalid', b'\xff', b'{"version": 77,"projects":[]}']:
            self.library.path.write_bytes(payload)
            with self.assertRaises(CorruptLibraryError) as caught:
                self.library.load()
            self.assertEqual(self.library.path.read_bytes(), payload)
            self.assertEqual(caught.exception.backup.read_bytes(), payload)
            with self.assertRaises(OSError):
                self.add()

    def test_malformed_entry_and_duplicate_ids_are_corrupt(self):
        p = self.add()
        data = json.loads(self.library.path.read_text(encoding='utf-8'))
        data['projects'].append(data['projects'][0])
        self.library.path.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaises(CorruptLibraryError):
            self.library.load()

    def test_missing_folder_can_be_loaded_but_not_previewed(self):
        p = self.add()
        (self.site / 'index.html').unlink()
        self.site.rmdir()
        self.library.load()
        self.assertEqual(len(self.library.projects), 1)
        with self.assertRaises(ValueError):
            self.manager.start(p)

    def test_two_real_http_servers_and_shutdown(self):
        p = self.add()
        other = self.root / 'other'
        other.mkdir()
        (other / 'index.html').write_text('SECOND SITE', encoding='utf-8')
        q = self.add(name='Second', folder=other)
        urls = [self.manager.start(p), self.manager.start(q)]
        self.assertNotEqual(*urls)
        self.assertEqual(self.manager.start(p), urls[0])
        for url, marker in zip(urls, [b'Bonjour DevDock', b'SECOND SITE']):
            self.assertTrue(url.startswith('http://127.0.0.1:'))
            with urlopen(url, timeout=3) as response:
                self.assertIn(marker, response.read())
        self.manager.stop(p.id)
        with self.assertRaises((URLError, OSError)):
            urlopen(urls[0], timeout=1)
        with urlopen(urls[1], timeout=3) as response:
            self.assertEqual(response.status, 200)
        self.manager.stop_all()
        self.assertFalse(self.manager.running)
        with self.assertRaises((URLError, OSError)):
            urlopen(urls[1], timeout=1)

    def test_launch_error_and_remove_preserve_files(self):
        p = self.add()
        with patch('core.ThreadingHTTPServer', side_effect=OSError('Bind refusé')):
            with self.assertRaises(OSError):
                self.manager.start(p)
        self.assertFalse(self.manager.running)
        self.library.remove(p.id)
        self.assertTrue((self.site / 'index.html').is_file())
        reloaded = Library(self.library.path)
        reloaded.load()
        self.assertFalse(reloaded.projects)


if __name__ == '__main__':
    unittest.main()
