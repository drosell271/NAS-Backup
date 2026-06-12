from __future__ import annotations

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMenu, QStyle, QSystemTrayIcon

from app.config import asset_path


class TrayService:
    def __init__(self, main_window, task_manager) -> None:
        self.main_window = main_window
        self.task_manager = task_manager
        self.should_quit = False
        icon_file = asset_path("icon.ico")
        icon = QIcon(str(icon_file)) if icon_file else main_window.style().standardIcon(QStyle.SP_DriveNetIcon)
        self.icon = QSystemTrayIcon(icon if not icon.isNull() else QIcon(), main_window)
        self.icon.setToolTip("NAS Backup")
        self.menu = QMenu(main_window)
        self._build_menu()
        self.icon.setContextMenu(self.menu)
        self.icon.activated.connect(self._on_activated)

    def _build_menu(self) -> None:
        show_action = QAction("Mostrar ventana", self.menu)
        show_action.triggered.connect(self.main_window.show_normal)
        run_all_action = QAction("Ejecutar todas ahora", self.menu)
        run_all_action.triggered.connect(self.task_manager.run_all_now)
        pause_all_action = QAction("Pausar todas", self.menu)
        pause_all_action.triggered.connect(self.task_manager.pause_all)
        resume_all_action = QAction("Reanudar todas", self.menu)
        resume_all_action.triggered.connect(self.task_manager.resume_all)
        settings_action = QAction("Preferencias", self.menu)
        settings_action.triggered.connect(self.main_window.open_settings)
        exit_action = QAction("Salir", self.menu)
        exit_action.triggered.connect(self.main_window.exit_application)

        self.menu.addAction(show_action)
        self.menu.addAction(run_all_action)
        self.menu.addSeparator()
        self.menu.addAction(pause_all_action)
        self.menu.addAction(resume_all_action)
        self.menu.addSeparator()
        self.menu.addAction(settings_action)
        self.menu.addSeparator()
        self.menu.addAction(exit_action)

    def show(self) -> None:
        self.icon.show()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self.main_window.show_normal()
