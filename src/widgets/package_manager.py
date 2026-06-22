from __future__ import annotations
import subprocess

from PySide6.QtCore import Qt, QProcess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QSplitter,
    QPlainTextEdit, QPushButton, QTabWidget,
    QAbstractItemView, QMessageBox,
)

from src.utils.syntax import ControlHighlighter


class PackageManagerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_installed_packages()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QVBoxLayout()
        title = QLabel("Package Manager")
        title.setObjectName("section-title")
        desc = QLabel("Browse, inspect, and analyze installed Debian packages")
        desc.setObjectName("section-desc")
        header.addWidget(title)
        header.addWidget(desc)
        layout.addLayout(header)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search installed packages...")
        self.search_input.textChanged.connect(self._filter_packages)
        search_layout.addWidget(self.search_input, 1)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_installed_packages)
        search_layout.addWidget(refresh_btn)

        layout.addLayout(search_layout)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("<b>Installed Packages</b>"))

        self.pkg_tree = QTreeWidget()
        self.pkg_tree.setHeaderLabels(["Package", "Version", "Status"])
        self.pkg_tree.header().setStretchLastSection(False)
        self.pkg_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.pkg_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.pkg_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.pkg_tree.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.pkg_tree.currentItemChanged.connect(self._show_package_details)
        self.pkg_tree.setStyleSheet("""
            QTreeWidget {
                background: #181825;
                border: 1px solid #313244;
                border-radius: 6px;
            }
            QTreeWidget::item { padding: 4px 8px; color: #cdd6f4; }
            QTreeWidget::item:selected { background: #45475a; }
        """)
        left_layout.addWidget(self.pkg_tree)

        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(QLabel("<b>Package Details</b>"))

        self.details_tabs = QTabWidget()

        self.info_view = QPlainTextEdit()
        self.info_view.setReadOnly(True)
        self.info_view.setStyleSheet("""
            QPlainTextEdit {
                background: #11111b;
                color: #a6e3a1;
                font-family: "JetBrains Mono", "Fira Code", monospace;
                font-size: 12px;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        ControlHighlighter(self.info_view.document())
        self.details_tabs.addTab(self.info_view, "Info")

        self.files_view = QPlainTextEdit()
        self.files_view.setReadOnly(True)
        self.files_view.setStyleSheet(self.info_view.styleSheet())
        self.details_tabs.addTab(self.files_view, "Installed Files")

        right_layout.addWidget(self.details_tabs)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)
        action_layout.addStretch()

        self.remove_btn = QPushButton("🗑 Remove Package")
        self.remove_btn.setEnabled(False)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background: #f38ba8;
                color: #1e1e2e;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover { background: #eba0ac; }
            QPushButton:disabled { background: #45475a; color: #6c7086; }
        """)
        self.remove_btn.clicked.connect(self._remove_package)
        action_layout.addWidget(self.remove_btn)

        self.remove_output = QLabel("")
        self.remove_output.setStyleSheet("color: #a6adc8; font-size: 12px; padding: 4px 0;")
        action_layout.addWidget(self.remove_output, 1)

        right_layout.addLayout(action_layout)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter, 1)

    def _load_installed_packages(self):
        self.pkg_tree.clear()
        self.all_packages: list[tuple[str, str]] = []
        try:
            result = subprocess.run(
                ["dpkg-query", "-W", "-f", "${Package}\t${Version}\t${Status}\n"],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        name = parts[0]
                        version = parts[1]
                        status = parts[2] if len(parts) > 2 else "unknown"
                        self.all_packages.append((name, version, status))
                        item = QTreeWidgetItem([name, version, status])
                        self.pkg_tree.addTopLevelItem(item)
        except Exception:
            item = QTreeWidgetItem(["dpkg not available", "", "error"])
            self.pkg_tree.addTopLevelItem(item)

    def _filter_packages(self, text: str):
        for i in range(self.pkg_tree.topLevelItemCount()):
            item = self.pkg_tree.topLevelItem(i)
            if not text or text.lower() in item.text(0).lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def _show_package_details(self, current, previous):
        if not current:
            self.remove_btn.setEnabled(False)
            return
        pkg_name = current.text(0)
        self._selected_package = pkg_name
        self.remove_btn.setEnabled(True)
        self.remove_output.setText("")
        self._load_package_info(pkg_name)
        self._load_package_files(pkg_name)

    def _load_package_info(self, pkg_name: str):
        try:
            result = subprocess.run(
                ["dpkg-query", "-s", pkg_name],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                self.info_view.setPlainText(result.stdout.strip())
            else:
                self.info_view.setPlainText(f"Package '{pkg_name}' not found")
        except Exception as e:
            self.info_view.setPlainText(f"Error: {e}")

    def _load_package_files(self, pkg_name: str):
        try:
            result = subprocess.run(
                ["dpkg-query", "-L", pkg_name],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                self.files_view.setPlainText(result.stdout.strip())
            else:
                self.files_view.setPlainText("No file list available")
        except Exception as e:
            self.files_view.setPlainText(f"Error: {e}")

    def _remove_package(self):
        pkg = getattr(self, '_selected_package', None)
        if not pkg:
            return

        reply = QMessageBox.question(
            self, "Remove Package",
            f"Permanently remove '{pkg}'?\n\nThis will purge all its files and config.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.remove_btn.setEnabled(False)
        self.remove_output.setText(f"Removing {pkg}...")

        proc = QProcess(self)
        proc.readyReadStandardOutput.connect(lambda: self._on_remove_output(proc))
        proc.readyReadStandardError.connect(lambda: self._on_remove_output(proc))
        proc.finished.connect(lambda code: self._on_remove_finished(code, pkg))

        proc.start("pkexec", ["dpkg", "--purge", pkg])

    def _on_remove_output(self, proc: QProcess):
        data = proc.readAll().data().decode("utf-8", errors="replace")
        if data.strip():
            self.remove_output.setText(data.strip()[-80:])

    def _on_remove_finished(self, code: int, pkg: str):
        if code == 0:
            self.remove_output.setText(f"✅ Removed: {pkg}")
            self.info_view.clear()
            self.files_view.clear()
            self._load_installed_packages()
        else:
            self.remove_output.setText(f"❌ Failed to remove {pkg}")
            self.remove_btn.setEnabled(True)
