"""Interface native DevDock. Les serveurs tournent hors du thread Qt."""
from pathlib import Path
import shutil
import sys

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QApplication, QButtonGroup, QDialog, QDialogButtonBox,
    QFileDialog, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget)

from core import Library, PreviewManager, Project


def resources() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def label(text: str, style: str = "") -> QLabel:
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    if style:
        widget.setObjectName(style)
    widget.setWordWrap(True)
    return widget


def button(text, callback, style=""):
    widget = QPushButton(text)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    if style:
        widget.setObjectName(style)
    widget.clicked.connect(callback)
    return widget


class JobSignals(QObject):
    done = Signal(object, str)


class Job(QRunnable):
    def __init__(self, action):
        super().__init__()
        self.action = action
        self.signals = JobSignals()

    def run(self):
        try:
            result = self.action()
        except Exception as exc:
            self.signals.done.emit(None, str(exc))
        else:
            self.signals.done.emit(result, "")


class ProjectDialog(QDialog):
    def __init__(self, library: Library, project: Project | None, parent=None):
        super().__init__(parent)
        self.library, self.project = library, project
        self.setWindowTitle("Modifier le projet" if project else "Ajouter un projet")
        self.setMinimumWidth(510)
        layout = QVBoxLayout(self)
        layout.addWidget(label(self.windowTitle(), "dialogTitle"))
        form = QFormLayout()
        self.name = QLineEdit(project.name if project else "")
        self.name.setPlaceholderText("Mon prochain projet")
        self.folder = QLineEdit(project.folder if project else "")
        self.folder.setPlaceholderText("Choisir un dossier local")
        self.github = QLineEdit(project.github if project else "")
        self.github.setPlaceholderText("https://github.com/proprietaire/depot")
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.folder)
        folder_row.addWidget(button("Parcourir…", self.browse))
        form.addRow("Nom", self.name)
        form.addRow("Dossier", folder_row)
        form.addRow("GitHub · facultatif", self.github)
        layout.addLayout(form)
        self.error = label("", "error")
        layout.addWidget(self.error)
        controls = QDialogButtonBox()
        controls.addButton("Annuler", QDialogButtonBox.ButtonRole.RejectRole)
        controls.addButton("Enregistrer", QDialogButtonBox.ButtonRole.AcceptRole)
        controls.accepted.connect(self.save)
        controls.rejected.connect(self.reject)
        layout.addWidget(controls)

    def browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Dossier du projet", self.folder.text())
        if folder:
            self.folder.setText(folder)
            if not self.name.text().strip():
                self.name.setText(Path(folder).name)

    def save(self):
        try:
            self.library.upsert(self.name.text(), self.folder.text(), self.github.text(), self.project.id if self.project else None)
        except (ValueError, OSError) as exc:
            self.error.setText(f"Enregistrement impossible : {exc}")
            return
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self, library: Library | None = None, seed_example: bool = True):
        super().__init__()
        self.library = library if library is not None else Library()
        self.previews = PreviewManager()
        self.running_urls = {}
        self.category = "all"
        self.busy = False
        self.closing = False
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.setWindowTitle("DevDock · its lizhy")
        self.resize(1180, 800)
        self.setMinimumSize(900, 620)
        self.startup_error = ""
        first_run = not self.library.path.exists()
        try:
            self.library.load()
            if seed_example and first_run:
                target = self.library.path.parent / "example"
                if not target.exists():
                    shutil.copytree(resources() / "example", target)
                self.library.upsert("Premier aperçu", str(target))
        except (OSError, ValueError) as exc:
            self.library.read_only = True
            self.startup_error = str(exc)

        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(218)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(24, 32, 24, 24)
        side.setSpacing(12)
        side.addWidget(label("D /", "brandMark"))
        side.addWidget(label("DevDock", "brand"))
        side.addWidget(label("VOTRE ATELIER LOCAL", "micro"))
        side.addSpacing(34)
        self.nav = QButtonGroup(self)
        for key, title in [("all", "Tous les projets"), ("favorites", "Favoris"), ("running", "En cours")]:
            nav_button = button(title, lambda checked=False, key=key: self.select_category(key), "nav")
            nav_button.setCheckable(True)
            nav_button.setChecked(key == "all")
            self.nav.addButton(nav_button)
            side.addWidget(nav_button)
        side.addStretch()
        side.addWidget(label("100 % LOCAL", "micro"))
        side.addWidget(label("its lizhy · Loghan", "muted"))
        side.addWidget(label("DevDock / version 1.0", "micro"))
        outer.addWidget(sidebar)
        main = QVBoxLayout()
        main.setContentsMargins(32, 32, 32, 20)
        main.setSpacing(18)
        main.addWidget(label("VOS IDÉES ONT UN POINT DE DÉPART.", "micro"))
        main.addWidget(label("Moins chercher.\nPlus créer.", "hero"))
        main.addWidget(label("Vos projets, vos dossiers et vos aperçus. Au même endroit.", "muted"))
        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher un nom ou un chemin…")
        self.search.setAccessibleName("Rechercher un projet")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.render)
        toolbar.addWidget(self.search, 1)
        self.add_button = button("+  Ajouter un projet", self.edit_project, "primary")
        toolbar.addWidget(self.add_button)
        main.addLayout(toolbar)
        self.count = label("", "micro")
        main.addWidget(self.count)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.cards = QWidget()
        self.grid = QGridLayout(self.cards)
        self.grid.setContentsMargins(0, 0, 6, 0)
        self.grid.setSpacing(16)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)
        scroll.setWidget(self.cards)
        main.addWidget(scroll, 1)
        self.status = label("Prêt. Aperçus HTML statiques uniquement.", "muted")
        main.addWidget(self.status)
        data_note = label(f"Bibliothèque : {self.library.path}", "micro")
        data_note.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        main.addWidget(data_note)
        outer.addLayout(main, 1)
        self.setCentralWidget(root)
        self.render()
        if self.startup_error:
            QTimer.singleShot(0, lambda: self.show_error("Lecture de la bibliothèque", self.startup_error))

    def show_error(self, title, message):
        self.status.setText(f"{title} : {message}")
        QMessageBox.critical(self, title, message)

    def select_category(self, category):
        self.category = category
        self.render()

    def edit_project(self, checked=False, project=None):
        if self.busy or self.library.read_only:
            return
        if project and project.id in self.running_urls:
            self.show_error("Projet en cours", "Arrêtez l’aperçu avant de modifier ce projet.")
            return
        dialog = ProjectDialog(self.library, project, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.status.setText("Projet enregistré.")
            self.render()

    def favorite(self, project):
        try:
            self.library.favorite(project.id)
        except (ValueError, OSError) as exc:
            self.show_error("Sauvegarde impossible", str(exc))
        self.render()

    def remove(self, project):
        answer = QMessageBox.question(self, "Retirer le projet", f"Retirer « {project.name} » de la bibliothèque ?\nSes fichiers resteront intacts.")
        if answer != QMessageBox.StandardButton.Yes:
            return
        def action():
            self.previews.stop(project.id)
            self.library.remove(project.id)
        self.run_job(action, "Retrait du projet…")

    def open_url(self, url):
        if not QDesktopServices.openUrl(url):
            self.show_error("Ouverture impossible", "Aucune application n’a pu ouvrir cette adresse.")

    def open_folder(self, project):
        if not Path(project.folder).is_dir():
            self.show_error("Dossier introuvable", project.folder)
            return
        self.open_url(QUrl.fromLocalFile(project.folder))

    def toggle_preview(self, project):
        if project.id in self.running_urls:
            self.run_job(lambda: self.previews.stop(project.id), "Arrêt de l’aperçu…")
        else:
            self.run_job(lambda: self.previews.start(project), "Démarrage de l’aperçu…")

    def run_job(self, action, message):
        if self.busy:
            return
        self.busy = True
        self.status.setText(message)
        self.render()
        self.job = Job(action)
        self.job.signals.done.connect(self.job_done)
        self.pool.start(self.job)

    def job_done(self, result, error):
        self.busy = False
        self.running_urls = {pid: self.previews.url(pid) for pid in self.previews.running}
        self.render()
        if error:
            self.show_error("Opération impossible", error)
        else:
            self.status.setText("Prêt. " + (f"{len(self.running_urls)} aperçu(s) en cours." if self.running_urls else "Aucun aperçu en cours."))
        if self.closing:
            self.close()

    def render(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()
        mutable = not self.busy and not self.library.read_only
        self.add_button.setEnabled(mutable)
        projects = self.library.search(self.search.text(), self.category, set(self.running_urls))
        self.count.setText(f"{len(projects):02d} PROJET(S)  /  {len(self.running_urls):02d} APERÇU(S) EN COURS")
        if not projects:
            self.grid.addWidget(label("Aucun projet ici.\nAjoutez un dossier ou ajustez votre recherche.", "empty"), 0, 0, 1, 2)
        for index, project in enumerate(projects):
            card = QFrame()
            card.setObjectName("card")
            box = QVBoxLayout(card)
            box.setContentsMargins(20, 18, 20, 18)
            box.setSpacing(12)
            heading = QHBoxLayout()
            heading.addWidget(label(project.name, "cardTitle"), 1)
            favorite = button("★" if project.favorite else "☆", lambda checked=False, p=project: self.favorite(p), "star")
            favorite.setAccessibleName("Retirer des favoris" if project.favorite else "Ajouter aux favoris")
            favorite.setEnabled(mutable)
            heading.addWidget(favorite)
            box.addLayout(heading)
            path_label = label(project.folder, "path")
            path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            box.addWidget(path_label)
            available = (Path(project.folder) / "index.html").is_file()
            running = project.id in self.running_urls
            state = "APERÇU EN COURS" if running else "WEB STATIQUE" if available else "DOSSIER / SANS APERÇU STATIQUE"
            box.addWidget(label(state, "micro"))
            actions = QHBoxLayout()
            actions.addWidget(button("Dossier", lambda checked=False, p=project: self.open_folder(p)))
            github = button("GitHub ↗", lambda checked=False, p=project: self.open_url(QUrl(p.github)))
            github.setEnabled(bool(project.github))
            actions.addWidget(github)
            box.addLayout(actions)
            preview = button("Arrêter l’aperçu" if running else "Démarrer l’aperçu", lambda checked=False, p=project: self.toggle_preview(p), "preview")
            preview.setEnabled(not self.busy and (running or available))
            preview.setToolTip("HTML/CSS/JavaScript uniquement. index.html doit être à la racine du dossier.")
            box.addWidget(preview)
            if running:
                url = self.running_urls[project.id]
                box.addWidget(label(url, "path"))
                box.addWidget(button("Voir l’aperçu ↗", lambda checked=False, u=url: self.open_url(QUrl(u)), "primary"))
            footer = QHBoxLayout()
            edit = button("Modifier", lambda checked=False, p=project: self.edit_project(project=p), "quiet")
            edit.setEnabled(mutable and not running)
            footer.addWidget(edit)
            footer.addStretch()
            remove = button("Retirer", lambda checked=False, p=project: self.remove(p), "quiet")
            remove.setEnabled(mutable)
            footer.addWidget(remove)
            box.addLayout(footer)
            self.grid.addWidget(card, index // 2, index % 2)

    def closeEvent(self, event):
        if self.busy:
            self.closing = True
            event.ignore()
        elif self.running_urls:
            self.closing = True
            event.ignore()
            self.run_job(self.previews.stop_all, "Fermeture des aperçus…")
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DevDock")
    app.setOrganizationName("its lizhy")
    app.setStyle("Fusion")
    try:
        app.setStyleSheet((resources() / "theme.qss").read_text(encoding="utf-8"))
    except OSError as exc:
        QMessageBox.critical(None, "Thème indisponible", str(exc))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
