from __future__ import annotations
import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QFileSystemModel, QTreeView, QSplitter,
    QHeaderView, QDialog, QFormLayout, QLineEdit, QComboBox,
    QCheckBox, QDialogButtonBox, QMessageBox, QMenu, QFrame,
    QAbstractItemView,
)

from src.models.package import PackageFile


class PermissionDialog(QDialog):
    def __init__(self, pkg_file: PackageFile | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("File Permissions")
        self.setMinimumWidth(350)
        self.pkg_file = pkg_file or PackageFile(source_path="", target_path="")

        layout = QFormLayout(self)

        self.target_path = QLineEdit(self.pkg_file.target_path)
        self.target_path.setPlaceholderText("/usr/share/myapp/file")
        layout.addRow("Target Path:", self.target_path)

        self.permissions = QComboBox()
        self.permissions.addItems(["644", "755", "600", "700", "444", "555"])
        self.permissions.setCurrentText(self.pkg_file.permissions)
        layout.addRow("Permissions:", self.permissions)

        self.owner = QLineEdit(self.pkg_file.owner)
        layout.addRow("Owner:", self.owner)

        self.group = QLineEdit(self.pkg_file.group)
        layout.addRow("Group:", self.group)

        self.is_conf = QCheckBox("Configuration file (conffile)")
        self.is_conf.setChecked(self.pkg_file.is_conf_file)
        layout.addRow("", self.is_conf)

        self.is_exec = QCheckBox("Executable")
        self.is_exec.setChecked(self.pkg_file.is_executable)
        layout.addRow("", self.is_exec)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_result(self) -> PackageFile:
        self.pkg_file.target_path = self.target_path.text().strip()
        self.pkg_file.permissions = self.permissions.currentText()
        self.pkg_file.owner = self.owner.text().strip() or "root"
        self.pkg_file.group = self.group.text().strip() or "root"
        self.pkg_file.is_conf_file = self.is_conf.isChecked()
        self.pkg_file.is_executable = self.is_exec.isChecked()
        return self.pkg_file


class FileManagerWidget(QWidget):
    files_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.files: list[PackageFile] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QVBoxLayout()
        title = QLabel("File Manager")
        title.setObjectName("section-title")
        desc = QLabel("Manage package files, permissions, and directory structure with visual drag-and-drop")
        desc.setObjectName("section-desc")
        header.addWidget(title)
        header.addWidget(desc)
        layout.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("<b>Filesystem Browser</b>"))

        self.fs_tree = QTreeView()
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath("/")
        self.fs_model.setNameFilterDisables(False)
        self.fs_tree.setModel(self.fs_model)
        self.fs_tree.setRootIndex(self.fs_model.index("/usr"))
        self.fs_tree.setDragEnabled(True)
        self.fs_tree.setAcceptDrops(False)
        self.fs_tree.setSortingEnabled(True)
        self.fs_tree.setAnimated(True)
        self.fs_tree.setIndentation(16)
        self.fs_tree.setColumnHidden(1, True)
        self.fs_tree.setColumnHidden(2, True)
        self.fs_tree.setColumnHidden(3, True)
        self.fs_tree.header().setStretchLastSection(False)
        self.fs_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        left_layout.addWidget(self.fs_tree)

        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(QLabel("<b>Package File Tree</b>"))

        self.pkg_tree = QTreeWidget()
        self.pkg_tree.setHeaderLabels(["Target Path", "Permissions", "Owner", "Type"])
        self.pkg_tree.setAcceptDrops(True)
        self.pkg_tree.setDragEnabled(False)
        self.pkg_tree.setDragDropMode(QAbstractItemView.DropOnly)
        self.pkg_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pkg_tree.customContextMenuRequested.connect(self._show_context_menu)
        self.pkg_tree.header().setStretchLastSection(False)
        self.pkg_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.pkg_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.pkg_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.pkg_tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        right_layout.addWidget(self.pkg_tree)

        # Override drag&drop in pkg_tree
        self.pkg_tree.setAcceptDrops(True)
        self.pkg_tree.dragEnterEvent = self._drag_enter
        self.pkg_tree.dragMoveEvent = self._drag_move
        self.pkg_tree.dropEvent = self._drop_event

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        add_file_btn = QPushButton("Add File")
        add_file_btn.clicked.connect(self._add_file)
        btn_layout.addWidget(add_file_btn)

        add_dir_btn = QPushButton("Add Directory")
        add_dir_btn.clicked.connect(self._add_dir)
        btn_layout.addWidget(add_dir_btn)

        btn_layout.addStretch()

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected)
        btn_layout.addWidget(remove_btn)

        right_layout.addLayout(btn_layout)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

    def _drag_enter(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _drag_move(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _drop_event(self, event: QDropEvent):
        mime = event.mimeData()
        if mime.hasUrls():
            for url in mime.urls():
                path = url.toLocalFile()
                if path:
                    self._add_file_from_source(path)
            event.acceptProposedAction()
            self._refresh_tree()

    def _add_file_from_source(self, source_path: str):
        p = Path(source_path)
        if p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    rel = f.relative_to(p)
                    self.files.append(PackageFile(
                        source_path=str(f),
                        target_path=f"/usr/share/{self._get_default_share()}/{rel}",
                        permissions="755" if os.access(f, os.X_OK) else "644",
                    ))
        else:
            self.files.append(PackageFile(
                source_path=source_path,
                target_path=f"/usr/share/{self._get_default_share()}/{p.name}",
                permissions="755" if os.access(p, os.X_OK) else "644",
            ))
        self._refresh_tree()
        self.files_changed.emit()

    def _get_default_share(self) -> str:
        return "myapp"

    def _add_file(self):
        from PySide6.QtWidgets import QFileDialog
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        for path in paths:
            p = Path(path)
            self.files.append(PackageFile(
                source_path=path,
                target_path=f"/usr/share/{self._get_default_share()}/{p.name}",
            ))
        self._refresh_tree()
        self.files_changed.emit()

    def _add_dir(self):
        from PySide6.QtWidgets import QInputDialog
        dir_path, ok = QInputDialog.getText(self, "Add Directory", "Target directory path:")
        if ok and dir_path.strip():
            self.files.append(PackageFile(
                source_path="",
                target_path=dir_path.strip(),
                permissions="755",
                is_directory=True,
            ))
            self._refresh_tree()
            self.files_changed.emit()

    def _remove_selected(self):
        items = self.pkg_tree.selectedItems()
        for item in items:
            data = item.data(0, Qt.UserRole)
            if data is not None and data in self.files:
                self.files.remove(data)
        self._refresh_tree()
        self.files_changed.emit()

    def _show_context_menu(self, pos):
        item = self.pkg_tree.itemAt(pos)
        if not item:
            return
        menu = QMenu()
        edit_act = menu.addAction("Edit Permissions...")
        remove_act = menu.addAction("Remove")
        action = menu.exec(self.pkg_tree.viewport().mapToGlobal(pos))
        data = item.data(0, Qt.UserRole)
        if action == edit_act and data in self.files:
            dlg = PermissionDialog(data, self)
            if dlg.exec():
                idx = self.files.index(data)
                self.files[idx] = dlg.get_result()
                self._refresh_tree()
                self.files_changed.emit()
        elif action == remove_act and data in self.files:
            self.files.remove(data)
            self._refresh_tree()
            self.files_changed.emit()

    def _refresh_tree(self):
        self.pkg_tree.clear()
        for f in self.files:
            item = QTreeWidgetItem()
            item.setText(0, f.target_path)
            item.setText(1, f.permissions)
            item.setText(2, f"{f.owner}:{f.group}")
            item.setText(3, "dir" if f.is_directory else "file")
            item.setData(0, Qt.UserRole, f)
            self.pkg_tree.addTopLevelItem(item)

    def get_files(self) -> list[PackageFile]:
        return self.files

    def set_files(self, files: list[PackageFile]) -> None:
        self.files = files
        self._refresh_tree()
