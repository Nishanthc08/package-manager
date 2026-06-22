from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QComboBox, QCheckBox, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTabWidget,
    QPlainTextEdit, QMessageBox, QSizePolicy,
)
from src.models.package import PackageConfig, Dependency, Section, Priority
from src.core.templates import get_template, list_templates, get_template_description
from src.core.validator import validate_config
from src.utils.syntax import BashHighlighter, ControlHighlighter


class DependencyEditor(QWidget):
    changed = Signal()

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.dependencies: list[Dependency] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header = QHBoxLayout()
        header.addWidget(QLabel(f"<b>{label}</b>"))
        header.addStretch()
        add_btn = QPushButton("+ Add")
        add_btn.setFixedWidth(80)
        add_btn.clicked.connect(self._add_dep)
        header.addWidget(add_btn)
        layout.addLayout(header)

        self.list_widget = QListWidget()
        self.list_widget.setMaximumHeight(120)
        layout.addWidget(self.list_widget)

    def _add_dep(self):
        from PySide6.QtWidgets import QDialog, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("Add Dependency")
        dlg.setMinimumWidth(400)
        form = QFormLayout(dlg)
        pkg_edit = QLineEdit()
        op_combo = QComboBox()
        op_combo.addItems(["", ">=", "<=", ">>", "<<", "=", ">", "<"])
        ver_edit = QLineEdit()
        form.addRow("Package:", pkg_edit)
        form.addRow("Version Operator:", op_combo)
        form.addRow("Version:", ver_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)
        if dlg.exec() == QDialog.Accepted and pkg_edit.text().strip():
            dep = Dependency(
                package=pkg_edit.text().strip(),
                operator=op_combo.currentText() or None,
                version=ver_edit.text().strip() or None,
            )
            self.dependencies.append(dep)
            self._refresh()
            self.changed.emit()

    def _refresh(self):
        self.list_widget.clear()
        for dep in self.dependencies:
            item = QListWidgetItem(str(dep))
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.list_widget.addItem(item)


class MaintainerScriptEditor(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.script_editors: dict[str, QPlainTextEdit] = {}
        for name in ["preinst", "postinst", "prerm", "postrm"]:
            editor = QPlainTextEdit()
            editor.setPlaceholderText(f"#!/bin/bash\n# {name} script\nset -e\n\necho \"Running {name}\"")
            editor.textChanged.connect(self.changed.emit)
            self.script_editors[name] = editor
            BashHighlighter(editor.document())
            self.tabs.addTab(editor, name)

        layout.addWidget(QLabel("<b>Maintainer Scripts</b>"))
        layout.addWidget(self.tabs)

    def get_scripts(self) -> dict[str, str]:
        return {name: editor.toPlainText() for name, editor in self.script_editors.items()}

    def set_scripts(self, scripts: dict[str, str]) -> None:
        for name, content in scripts.items():
            if name in self.script_editors:
                self.script_editors[name].setPlainText(content)


class PackageWizard(QWidget):
    package_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = PackageConfig()
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        header = QVBoxLayout()
        title = QLabel("Package Builder")
        title.setObjectName("section-title")
        desc = QLabel("Create and configure Debian packages with an intuitive step-by-step interface")
        desc.setObjectName("section-desc")
        header.addWidget(title)
        header.addWidget(desc)
        main_layout.addLayout(header)

        content = QHBoxLayout()
        content.setSpacing(16)

        left_panel = QWidget()
        left_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(12)

        template_bar = QHBoxLayout()
        template_bar.addWidget(QLabel("Template:"))
        self.template_combo = QComboBox()
        self.template_combo.addItem("Blank Package", "empty")
        for tpl in list_templates():
            if tpl != "empty":
                self.template_combo.addItem(f"{tpl} - {get_template_description(tpl)}", tpl)
        self.template_combo.currentIndexChanged.connect(self._load_template)
        template_bar.addWidget(self.template_combo, 1)
        left_layout.addLayout(template_bar)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #313244; border-radius: 6px; background: #181825; padding: 12px; }
            QTabBar::tab { padding: 8px 16px; background: #181825; color: #a6adc8; border: none; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #313244; color: #fff; }
            QTabBar::tab:hover { background: #45475a; }
        """)

        self.tabs.addTab(self._build_basic_tab(), "Basic Info")
        self.tabs.addTab(self._build_deps_tab(), "Dependencies")
        self.tabs.addTab(self._build_scripts_tab(), "Scripts")
        left_layout.addWidget(self.tabs)

        content.addWidget(left_panel, 3)

        right_panel = QWidget()
        right_panel.setFixedWidth(420)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(QLabel("<b>Control File Preview</b>"))

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
        ControlHighlighter(self.preview.document())
        right_layout.addWidget(self.preview, 1)

        validate_btn = QPushButton("Validate Package")
        validate_btn.clicked.connect(self._validate)
        right_layout.addWidget(validate_btn)

        content.addWidget(right_panel)
        main_layout.addLayout(content)

    def _build_basic_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.pkg_name = QLineEdit()
        self.pkg_name.setPlaceholderText("e.g., my-application")
        self.pkg_name.textChanged.connect(self._update_preview)
        form.addRow("Package Name:", self.pkg_name)

        self.version = QLineEdit("1.0.0")
        self.version.textChanged.connect(self._update_preview)
        form.addRow("Version:", self.version)

        self.maintainer = QLineEdit()
        self.maintainer.setPlaceholderText("Your Name")
        self.maintainer.textChanged.connect(self._update_preview)
        form.addRow("Maintainer:", self.maintainer)

        self.email = QLineEdit()
        self.email.setPlaceholderText("you@example.com")
        self.email.textChanged.connect(self._update_preview)
        form.addRow("Email:", self.email)

        self.description = QLineEdit()
        self.description.setPlaceholderText("Short description (under 60 chars recommended)")
        self.description.textChanged.connect(self._update_preview)
        form.addRow("Description:", self.description)

        self.long_desc = QTextEdit()
        self.long_desc.setMaximumHeight(100)
        self.long_desc.setPlaceholderText("Long description (optional)")
        self.long_desc.textChanged.connect(self._update_preview)
        form.addRow("Long Description:", self.long_desc)

        self.arch = QComboBox()
        self.arch.addItems(["amd64", "i386", "arm64", "armhf", "all", "armel", "mips64el", "ppc64el", "s390x", "riscv64"])
        self.arch.currentTextChanged.connect(self._update_preview)
        form.addRow("Architecture:", self.arch)

        self.section = QComboBox()
        self.section.addItems([s.value for s in Section])
        self.section.currentTextChanged.connect(self._update_preview)
        form.addRow("Section:", self.section)

        self.priority = QComboBox()
        self.priority.addItems([p.value for p in Priority])
        self.priority.currentTextChanged.connect(self._update_preview)
        form.addRow("Priority:", self.priority)

        self.essential = QCheckBox("Essential package")
        self.essential.toggled.connect(self._update_preview)
        form.addRow("", self.essential)

        self.homepage = QLineEdit()
        self.homepage.setPlaceholderText("https://example.com")
        self.homepage.textChanged.connect(self._update_preview)
        form.addRow("Homepage:", self.homepage)

        return w

    def _build_deps_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(8)

        self.dep_editors: dict[str, DependencyEditor] = {}
        for label in ["Depends", "Recommends", "Suggests", "Pre-Depends", "Breaks", "Conflicts", "Provides", "Replaces"]:
            ed = DependencyEditor(label)
            ed.changed.connect(self._update_preview)
            self.dep_editors[label] = ed
            layout.addWidget(ed)

        layout.addStretch()
        return w

    def _build_scripts_tab(self) -> QWidget:
        self.script_editor = MaintainerScriptEditor()
        self.script_editor.changed.connect(self._update_preview)
        return self.script_editor

    def _load_template(self):
        tpl_name = self.template_combo.currentData()
        if not tpl_name or tpl_name == "empty":
            return
        tpl = get_template(tpl_name)
        if tpl:
            self._apply_config(tpl)

    def _apply_config(self, cfg: PackageConfig):
        self.pkg_name.setText(cfg.package_name)
        self.version.setText(cfg.version)
        self.maintainer.setText(cfg.maintainer)
        self.email.setText(cfg.email)
        self.description.setText(cfg.description)
        self.long_desc.setPlainText(cfg.long_description)

        idx = self.arch.findText(cfg.architecture)
        if idx >= 0:
            self.arch.setCurrentIndex(idx)

        idx = self.section.findText(cfg.section)
        if idx >= 0:
            self.section.setCurrentIndex(idx)

        idx = self.priority.findText(cfg.priority)
        if idx >= 0:
            self.priority.setCurrentIndex(idx)

        self.essential.setChecked(cfg.essential)
        self.homepage.setText(cfg.homepage)

        self._update_preview()

    def _update_preview(self):
        self._sync_config()
        self.preview.setPlainText(self.config.generate_control())

    def _sync_config(self):
        self.config.package_name = self.pkg_name.text().strip()
        self.config.version = self.version.text().strip()
        self.config.maintainer = self.maintainer.text().strip()
        self.config.email = self.email.text().strip()
        self.config.description = self.description.text().strip()
        self.config.long_description = self.long_desc.toPlainText().strip()
        self.config.architecture = self.arch.currentText().strip()
        self.config.section = self.section.currentText().strip()
        self.config.priority = self.priority.currentText().strip()
        self.config.essential = self.essential.isChecked()
        self.config.homepage = self.homepage.text().strip()
        self.config.maintainer_scripts = self.script_editor.get_scripts()

    def _validate(self):
        self._sync_config()
        result = validate_config(self.config)
        if result.is_valid:
            QMessageBox.information(self, "Validation", "Package configuration is valid!")
        else:
            msg = "<b>Errors:</b><br>" + "<br>".join(
                f"• {e['field']}: {e['message']}" for e in result.errors
            )
            if result.warnings:
                msg += "<br><br><b>Warnings:</b><br>" + "<br>".join(
                    f"• {w['field']}: {w['message']}" for w in result.warnings
                )
            QMessageBox.warning(self, "Validation Results", msg)

    def get_config(self) -> PackageConfig:
        self._sync_config()
        return self.config
