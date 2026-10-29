"""Bibliothèque locale et aperçus statiques, indépendants de Qt."""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from threading import Thread
from urllib.parse import urlsplit
from uuid import uuid4


def data_directory() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "DevDock"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "DevDock"


def github_url(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    parts = urlsplit(value)
    if (parts.scheme != "https" or parts.netloc.lower() != "github.com"
            or parts.query or parts.fragment
            or not re.fullmatch(r"/[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+/?", parts.path)):
        raise ValueError("Lien GitHub invalide. Utilisez https://github.com/proprietaire/depot.")
    owner, repo = parts.path.strip("/").split("/")
    if repo.endswith(".git"):
        repo = repo[:-4]
    if repo in ("", ".", ".."):
        raise ValueError("Le nom du dépôt GitHub est invalide.")
    return f"https://github.com/{owner}/{repo}"


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    folder: str
    github: str = ""
    favorite: bool = False


class CorruptLibraryError(ValueError):
    """Le fichier original reste intact ; backup contient sa copie si possible."""
    def __init__(self, path: Path, backup: Path | None, reason: str):
        self.backup = backup
        super().__init__(f"Bibliothèque illisible : {path}\n{reason}\n"
                         + (f"Copie préservée : {backup}" if backup else "Original conservé ; copie de sauvegarde impossible.")
                         + "\nCorrigez ou déplacez le fichier original, puis relancez DevDock. Aucune écriture autorisée entre-temps.")


class Library:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else data_directory() / "library.json"
        self.projects: list[Project] = []
        self.read_only = False

    def load(self) -> None:
        try:
            raw = self.path.read_bytes()
        except FileNotFoundError:
            self.projects = []
            return
        try:
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1 or not isinstance(data.get("projects"), list):
                raise ValueError("Format ou version de bibliothèque non reconnu.")
            projects, ids, folders = [], set(), set()
            for entry in data["projects"]:
                if not isinstance(entry, dict) or set(entry) != {"id", "name", "folder", "github", "favorite"}:
                    raise ValueError("Entrée de projet invalide.")
                if not all(isinstance(entry[k], str) for k in ("id", "name", "folder", "github")) or type(entry["favorite"]) is not bool:
                    raise ValueError("Types de données invalides.")
                p = Project(**entry)
                if not p.id or not p.name.strip() or not Path(p.folder).is_absolute():
                    raise ValueError("Nom, identifiant ou chemin invalide.")
                github_url(p.github)
                key = os.path.normcase(str(Path(p.folder).resolve()))
                if p.id in ids or key in folders:
                    raise ValueError("Projets en double.")
                ids.add(p.id)
                folders.add(key)
                projects.append(p)
            self.projects = projects
        except (ValueError, TypeError, OSError) as exc:
            self.read_only = True
            backup = self.path.with_name(f"{self.path.name}.corrupt-{uuid4().hex}.bak")
            try:
                shutil.copy2(self.path, backup)
            except OSError:
                backup = None
            raise CorruptLibraryError(self.path, backup, str(exc)) from exc
        self.read_only = False

    def _commit(self, projects: list[Project]) -> None:
        if self.read_only:
            raise OSError("Bibliothèque protégée après une erreur de lecture. Corrigez le fichier puis relancez.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, prefix=".library-", suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                json.dump({"version": 1, "projects": [asdict(p) for p in projects]}, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        self.projects = projects

    def upsert(self, name: str, folder: str, github: str = "", project_id: str | None = None) -> Project:
        name = name.strip()
        if not name:
            raise ValueError("Indiquez un nom de projet.")
        path = Path(folder).expanduser().resolve()
        if not folder.strip() or not path.is_dir():
            raise ValueError("Le dossier sélectionné n’existe pas.")
        current = self.get(project_id) if project_id else None
        key = os.path.normcase(str(path))
        if any(os.path.normcase(str(Path(p.folder).resolve())) == key and p.id != project_id for p in self.projects):
            raise ValueError("Ce dossier est déjà dans votre bibliothèque.")
        project = Project(project_id or uuid4().hex, name, str(path), github_url(github), current.favorite if current else False)
        self._commit([project if p.id == project_id else p for p in self.projects] if current else [*self.projects, project])
        return project

    def get(self, project_id: str) -> Project:
        return next(p for p in self.projects if p.id == project_id)

    def favorite(self, project_id: str) -> None:
        current = self.get(project_id)
        self._commit([replace(p, favorite=not current.favorite) if p.id == project_id else p for p in self.projects])

    def remove(self, project_id: str) -> None:
        self.get(project_id)
        self._commit([p for p in self.projects if p.id != project_id])

    def search(self, text: str = "", category: str = "all", running: set[str] | None = None) -> list[Project]:
        text = text.strip().casefold()
        return sorted((p for p in self.projects
                       if (not text or text in p.name.casefold() or text in p.folder.casefold())
                       and (category != "favorites" or p.favorite)
                       and (category != "running" or p.id in (running or set()))), key=lambda p: p.name.casefold())


class StaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def send_head(self):
        # Empêche également les liens symboliques de servir des fichiers hors projet.
        target = Path(self.translate_path(self.path)).resolve()
        if not target.is_relative_to(Path(self.directory).resolve()):
            self.send_error(403, "Hors du dossier projet")
            return None
        return super().send_head()


class PreviewManager:
    """Adaptateur statique v1. D'autres lanceurs pourront avoir la même API."""
    def __init__(self):
        self._servers: dict[str, tuple[ThreadingHTTPServer, Thread]] = {}

    @property
    def running(self) -> set[str]:
        return set(self._servers)

    def url(self, project_id: str) -> str:
        server, _ = self._servers[project_id]
        return f"http://127.0.0.1:{server.server_port}/"

    def start(self, project: Project) -> str:
        if project.id in self._servers:
            return self.url(project.id)
        folder = Path(project.folder)
        if not folder.is_dir() or not (folder / "index.html").is_file():
            raise ValueError("Aperçu statique indisponible : le dossier doit contenir index.html à sa racine.")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(StaticHandler, directory=str(folder)))
        server.daemon_threads = True
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True, name=f"DevDock-{project.id}")
        try:
            thread.start()
        except Exception:
            server.server_close()
            raise
        self._servers[project.id] = server, thread
        return self.url(project.id)

    def stop(self, project_id: str) -> None:
        entry = self._servers.get(project_id)
        if entry:
            server, thread = entry
            server.shutdown()
            server.server_close()
            thread.join()
            del self._servers[project_id]

    def stop_all(self) -> None:
        for project_id in list(self._servers):
            self.stop(project_id)
