import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.request import urlopen

from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton
from app import MainWindow, ProjectDialog, resources
from core import Library

APP = QApplication.instance() or QApplication([])
APP.setStyle('Fusion')
APP.setStyleSheet((resources() / 'theme.qss').read_text(encoding='utf-8'))


def wait_until(condition):
    deadline = time.monotonic() + 8
    while not condition():
        APP.processEvents()
        QTest.qWait(10)
        if time.monotonic() > deadline:
            raise AssertionError('Délai Qt dépassé')
    APP.processEvents()


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.window = MainWindow(Library(self.root / 'data' / 'library.json'), seed_example=False)
        self.window.show()
        APP.processEvents()

    def tearDown(self):
        self.window.close()
        wait_until(lambda: not self.window.isVisible())
        self.window.pool.waitForDone()
        self.temp.cleanup()

    def add_site(self, name='Projet Qt'):
        folder = self.root / name
        folder.mkdir()
        (folder / 'index.html').write_text('QT REAL HTTP', encoding='utf-8')
        return self.window.library.upsert(name, str(folder))

    def test_real_dialog_validation_add_edit_and_search(self):
        p = self.add_site()
        dialog = ProjectDialog(self.window.library, p, self.window)
        dialog.show()
        dialog.name.setText('')
        dialog.save()
        self.assertIn('impossible', dialog.error.text())
        dialog.name.setText('Renommé depuis Qt')
        dialog.save()
        self.assertEqual(dialog.result(), ProjectDialog.DialogCode.Accepted)
        self.window.render()
        self.window.search.setText('absent')
        self.assertIn('00 PROJET', self.window.count.text())
        self.window.search.setText('renommé')
        self.assertIn('01 PROJET', self.window.count.text())
        self.window.favorite(self.window.library.get(p.id))
        self.window.select_category('favorites')
        self.assertIn('01 PROJET', self.window.count.text())

    def test_two_previews_ui_responsive_and_close_stops_all(self):
        first, second = self.add_site('Un'), self.add_site('Deux')
        heartbeats = []
        timer = QTimer()
        timer.timeout.connect(lambda: heartbeats.append(1))
        timer.start(5)
        self.window.toggle_preview(first)
        wait_until(lambda: not self.window.busy)
        self.window.toggle_preview(second)
        wait_until(lambda: not self.window.busy)
        self.assertEqual(len(self.window.running_urls), 2)
        for url in self.window.running_urls.values():
            with urlopen(url, timeout=3) as response:
                self.assertIn(b'QT REAL HTTP', response.read())
        self.window.select_category('running')
        self.assertIn('02 PROJET', self.window.count.text())
        self.window.close()
        wait_until(lambda: not self.window.isVisible())
        timer.stop()
        self.assertTrue(heartbeats)
        self.assertEqual(self.window.previews.running, set())

    def test_remove_via_confirmation_preserves_files(self):
        p = self.add_site()
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            self.window.remove(p)
            wait_until(lambda: not self.window.busy)
        self.assertEqual(self.window.library.projects, [])
        self.assertTrue((Path(p.folder) / 'index.html').is_file())

    def test_errors_are_displayed_and_failed_save_is_not_committed(self):
        p = self.add_site()
        with patch.object(QMessageBox, 'critical') as message:
            with patch.object(self.window.previews, 'start', side_effect=OSError('Port interdit')):
                self.window.toggle_preview(p)
                wait_until(lambda: not self.window.busy)
            self.assertIn('Port interdit', message.call_args.args[-1])
            with patch('core.os.replace', side_effect=PermissionError('Écriture refusée')):
                self.window.favorite(p)
            self.assertIn('Écriture refusée', message.call_args.args[-1])
        self.assertFalse(self.window.library.get(p.id).favorite)

    def test_corrupt_library_shows_error_and_disables_add(self):
        path = self.root / 'bad.json'
        path.write_bytes(b'{broken')
        with patch.object(QMessageBox, 'critical') as message:
            broken = MainWindow(Library(path), seed_example=False)
            APP.processEvents()
            self.assertTrue(message.called)
            self.assertFalse(broken.add_button.isEnabled())
            self.assertEqual(path.read_bytes(), b'{broken')
            broken.close()

    def test_first_run_example_is_copied_outside_application(self):
        seeded = MainWindow(Library(self.root / 'seed' / 'library.json'))
        p = seeded.library.projects[0]
        self.assertTrue((Path(p.folder) / 'index.html').is_file())
        self.assertTrue(Path(p.folder).is_relative_to(self.root))
        seeded.close()


if __name__ == '__main__':
    unittest.main()
