from __future__ import annotations
import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPlainTextEdit, QSplitter, QPushButton,
    QMessageBox, QFileDialog,
)

from src.core.templates import get_template, list_templates, get_template_description


class TemplateManagerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QVBoxLayout()
        title = QLabel("Template Manager")
        title.setObjectName("section-title")
        desc = QLabel("Browse, create, export, and import package templates for rapid development")
        desc.setObjectName("section-desc")
        header.addWidget(title)
        header.addWidget(desc)
        layout.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("<b>Available Templates</b>"))

        self.template_list = QListWidget()
        self.template_list.setStyleSheet("""
            QListWidget {
                background: #181825;
                border: 1px solid #313244;
                border-radius: 6px;
            }
            QListWidget::item {
                padding: 10px 12px;
                border-bottom: 1px solid #313244;
                color: #cdd6f4;
            }
            QListWidget::item:selected {
                background: #45475a;
                color: #fff;
            }
            QListWidget::item:hover { background: #313244; }
        """)
        self._populate_templates()
        self.template_list.currentRowChanged.connect(self._show_template)
        left_layout.addWidget(self.template_list, 1)

        actions = QHBoxLayout()
        import_btn = QPushButton("Import Template...")
        import_btn.clicked.connect(self._import_template)
        actions.addWidget(import_btn)

        export_btn = QPushButton("Export Selected...")
        export_btn.clicked.connect(self._export_template)
        actions.addWidget(export_btn)

        delete_btn = QPushButton("Delete Custom")
        delete_btn.clicked.connect(self._delete_template)
        actions.addWidget(delete_btn)

        left_layout.addLayout(actions)
        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(QLabel("<b>Template Preview</b>"))

        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setStyleSheet("""
            QPlainTextEdit {
                background: #11111b;
                color: #a6e3a1;
                font-family: "JetBrains Mono", "Fira Code", "Consolas", monospace;
                font-size: 12px;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        right_layout.addWidget(self.preview, 1)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter, 1)

    def _populate_templates(self):
        self.template_list.clear()
        for tpl in list_templates():
            item = QListWidgetItem(f"{tpl} - {get_template_description(tpl)}")
            item.setData(Qt.UserRole, tpl)
            self.template_list.addItem(item)

    def _show_template(self, row: int):
        if row < 0:
            self.preview.clear()
            return
        item = self.template_list.item(row)
        if not item:
            return
        tpl_name = item.data(Qt.UserRole)
        tpl = get_template(tpl_name)
        if tpl:
            self.preview.setPlainText(tpl.generate_control())

    def _export_template(self):
        row = self.template_list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Export", "Please select a template first.")
            return
        item = self.template_list.item(row)
        tpl_name = item.data(Qt.UserRole)
        tpl = get_template(tpl_name)
        if not tpl:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Template", f"{tpl_name}.json", "JSON Files (*.json)"
        )
        if path:
            try:
                data = {
                    "template_name": tpl_name,
                    "config": {
                        "package_name": tpl.package_name,
                        "version": tpl.version,
                        "maintainer": tpl.maintainer,
                        "email": tpl.email,
                        "description": tpl.description,
                        "long_description": tpl.long_description,
                        "architecture": tpl.architecture,
                        "section": tpl.section,
                        "priority": tpl.priority,
                        "essential": tpl.essential,
                        "homepage": tpl.homepage,
                        "depends": [str(d) for d in tpl.depends],
                        "recommends": [str(d) for d in tpl.recommends],
                        "suggests": [str(d) for d in tpl.suggests],
                    },
                }
                with open(path, "w") as f:
                    json.dump(data, f, indent=2)
                QMessageBox.information(self, "Export", f"Template exported to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {e}")

    def _import_template(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Template", "", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            with open(path) as f:
                data = json.load(f)
            QMessageBox.information(
                self, "Import",
                f"Template '{data.get('template_name', 'unknown')}' imported successfully!\n"
                "Use it from the Package Builder's template dropdown."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {e}")

    def _delete_template(self):
        row = self.template_list.currentRow()
        if row < 0:
            return
        item = self.template_list.item(row)
        tpl_name = item.data(Qt.UserRole)
        if tpl_name in ("empty",):
            QMessageBox.information(self, "Delete", "Built-in templates cannot be deleted.")
            return
        reply = QMessageBox.question(
            self, "Delete Template",
            f"Delete template '{tpl_name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.template_list.takeItem(row)
