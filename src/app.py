from __future__ import annotations
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel,
    QStatusBar, QToolBar, QMenu, QMenuBar, QMessageBox, QSplitter,
    QFrame, QPushButton, QSizePolicy,
)

from src.widgets.wizard import PackageWizard
from src.widgets.file_manager import FileManagerWidget
from src.widgets.build_pipeline import BuildPipelineWidget
from src.widgets.package_manager import PackageManagerWidget
from src.widgets.repo_manager import RepoManagerWidget
from src.widgets.template_manager import TemplateManagerWidget


SIDEBAR_ITEMS = [
    ("package", "Package Builder"),
    ("files", "File Manager"),
    ("build", "Build Pipeline"),
    ("packages", "Package Manager"),
    ("repo", "Repository Manager"),
    ("templates", "Templates"),
]


class SidebarButton(QPushButton):
    def __init__(self, text: str, icon_char: str = ""):
        super().__init__()
        self.setText(f"  {icon_char} {text}" if icon_char else f"  {text}")
        self.setCheckable(True)
        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                background: transparent;
                color: #ccc;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.08);
                color: #fff;
            }
            QPushButton:checked {
                background: rgba(74, 144, 226, 0.3);
                color: #fff;
                font-weight: bold;
            }
        """)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Boss Package Manager")
        self.resize(1280, 820)
        self.setMinimumSize(960, 600)

        self._setup_style()
        self._setup_menu()
        self._setup_ui()
        self._setup_status_bar()

    def _setup_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: "Segoe UI", "Ubuntu", "Helvetica Neue", sans-serif;
            }
            QListWidget {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #45475a;
                color: #fff;
            }
            QListWidget::item:hover {
                background-color: #313244;
            }
            QStackedWidget {
                background-color: #1e1e2e;
            }
            QLabel#section-title {
                font-size: 22px;
                font-weight: bold;
                color: #fff;
                padding: 0px;
            }
            QLabel#section-desc {
                font-size: 13px;
                color: #a6adc8;
                padding: 0px;
            }
        """)

    def _setup_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar { background: #181825; color: #cdd6f4; border-bottom: 1px solid #313244; }
            QMenuBar::item:selected { background: #313244; }
            QMenu { background: #1e1e2e; border: 1px solid #313244; color: #cdd6f4; }
            QMenu::item:selected { background: #45475a; }
        """)

        file_menu = menubar.addMenu("&File")
        new_act = QAction("&New Package", self)
        new_act.setShortcut(QKeySequence.New)
        new_act.triggered.connect(lambda: self._switch_page(0))
        file_menu.addAction(new_act)

        open_act = QAction("&Open Package...", self)
        open_act.setShortcut(QKeySequence.Open)
        file_menu.addAction(open_act)
        file_menu.addSeparator()

        import_act = QAction("&Import Config...", self)
        file_menu.addAction(import_act)
        export_act = QAction("&Export Config...", self)
        file_menu.addAction(export_act)
        file_menu.addSeparator()

        quit_act = QAction("&Quit", self)
        quit_act.setShortcut(QKeySequence.Quit)
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        build_menu = menubar.addMenu("&Build")
        build_act = QAction("&Build Package", self)
        build_act.setShortcut(QKeySequence("Ctrl+B"))
        build_act.triggered.connect(lambda: self._switch_page(2))
        build_menu.addAction(build_act)

        queue_act = QAction("&Build Queue...", self)
        build_menu.addAction(queue_act)

        view_menu = menubar.addMenu("&View")
        for i, (key, label) in enumerate(SIDEBAR_ITEMS):
            act = QAction(label, self)
            act.setShortcut(QKeySequence(f"Ctrl+{i + 1}"))
            act.triggered.connect(lambda checked, idx=i: self._switch_page(idx))
            view_menu.addAction(act)

        help_menu = menubar.addMenu("&Help")
        about_act = QAction("&About Boss Package Manager", self)
        about_act.triggered.connect(self._show_about)
        help_menu.addAction(about_act)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background: #181825; border-radius: 10px;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 16, 8, 16)
        sidebar_layout.setSpacing(4)

        logo = QLabel("📦 Boss Package Manager")
        logo.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff; padding: 8px 12px; margin-bottom: 12px;")
        sidebar_layout.addWidget(logo)

        self.sidebar_buttons: list[SidebarButton] = []
        icons = ["📦", "📁", "🔨", "📋", "🏪", "📄"]
        for i, (key, label) in enumerate(SIDEBAR_ITEMS):
            btn = SidebarButton(label, icons[i] if i < len(icons) else "")
            btn.clicked.connect(lambda checked, idx=i: self._switch_page(idx))
            self.sidebar_buttons.append(btn)
            sidebar_layout.addWidget(btn)
            if i == 2:
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setStyleSheet("color: #313244; margin: 8px 0;")
                sidebar_layout.addWidget(sep)

        sidebar_layout.addStretch()

        self.stack = QStackedWidget()

        self.pages = []
        page_classes = [
            PackageWizard,
            FileManagerWidget,
            BuildPipelineWidget,
            PackageManagerWidget,
            RepoManagerWidget,
            TemplateManagerWidget,
        ]
        for cls in page_classes:
            page = cls(self)
            self.pages.append(page)
            self.stack.addWidget(page)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(sidebar)
        splitter.addWidget(self.stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background: #313244; }")

        main_layout.addWidget(splitter)

        self.sidebar_buttons[0].setChecked(True)

    def _setup_status_bar(self):
        self.status = QStatusBar()
        self.status.setStyleSheet("""
            QStatusBar {
                background: #181825;
                border-top: 1px solid #313244;
                color: #a6adc8;
                font-size: 12px;
                padding: 4px 12px;
            }
        """)
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

    def _switch_page(self, idx: int):
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self.sidebar_buttons):
            btn.setChecked(i == idx)

    def _show_about(self):
        QMessageBox.about(
            self,
            "About Boss Package Manager",
            "<h3>Boss Package Manager 1.0</h3>"
            "<p>A professional desktop application for building and managing Debian packages.</p>"
            "<p>Built with Python, PySide6, and love for Debian packaging.</p>"
        )

    def status_message(self, msg: str, timeout: int = 5000):
        self.status.showMessage(msg, timeout)


def run():
    app = QApplication(sys.argv)
    app.setApplicationName("Boss Package Manager")
    app.setOrganizationName("DPKGBuilder")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
