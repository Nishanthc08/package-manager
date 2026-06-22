from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QFormLayout, QFileDialog, QMessageBox, QTextEdit,
    QSplitter, QCheckBox, QAbstractItemView, QComboBox, QFrame,
)

from src.models.build import RepositoryConfig
from src.utils.helpers import run_command


class RepoManagerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = RepositoryConfig()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QVBoxLayout()
        title = QLabel("Repository Manager")
        title.setObjectName("section-title")
        desc = QLabel("Create, manage, and sign local APT repositories")
        desc.setObjectName("section-desc")
        header.addWidget(title)
        header.addWidget(desc)
        layout.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        repo_group = QGroupBox("Repository Configuration")
        repo_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #313244;
                border-radius: 8px;
                margin-top: 12px;
                padding: 16px 12px 12px 12px;
                font-weight: bold;
                color: #cdd6f4;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
        """)
        repo_form = QFormLayout(repo_group)
        repo_form.setSpacing(8)

        self.repo_name = QLineEdit()
        self.repo_name.setPlaceholderText("e.g., myrepo")
        repo_form.addRow("Name:", self.repo_name)

        self.repo_path = QLineEdit()
        self.repo_path.setPlaceholderText("/var/www/repo or /home/user/repo")
        repo_browse = QPushButton("Browse...")
        repo_browse.clicked.connect(self._browse_repo_path)
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.repo_path, 1)
        path_layout.addWidget(repo_browse)
        repo_form.addRow("Path:", path_layout)

        self.repo_desc = QLineEdit()
        self.repo_desc.setPlaceholderText("My local APT repository")
        repo_form.addRow("Description:", self.repo_desc)

        self.repo_origin = QLineEdit()
        self.repo_origin.setPlaceholderText("Your Name/Org")
        repo_form.addRow("Origin:", self.repo_origin)

        self.repo_label = QLineEdit()
        self.repo_label.setPlaceholderText("My Repository")
        repo_form.addRow("Label:", self.repo_label)

        self.repo_suite = QComboBox()
        self.repo_suite.addItems(["stable", "testing", "unstable", "bookworm", "bullseye", "jammy", "noble"])
        repo_form.addRow("Suite:", self.repo_suite)

        self.repo_component = QComboBox()
        self.repo_component.addItems(["main", "contrib", "non-free", "non-free-firmware"])
        repo_form.addRow("Component:", self.repo_component)

        left_layout.addWidget(repo_group)

        gpg_group = QGroupBox("GPG Signing (Optional)")
        gpg_group.setStyleSheet(repo_group.styleSheet())
        gpg_form = QFormLayout(gpg_group)
        gpg_form.setSpacing(8)

        self.gpg_key = QLineEdit()
        self.gpg_key.setPlaceholderText("GPG key ID or email")
        gpg_form.addRow("Key ID:", self.gpg_key)

        self.gpg_file = QLineEdit()
        self.gpg_file.setPlaceholderText("/path/to/private-key.asc")
        gpg_key_browse = QPushButton("Browse...")
        gpg_key_browse.clicked.connect(self._browse_gpg_key)
        gpg_path_layout = QHBoxLayout()
        gpg_path_layout.addWidget(self.gpg_file, 1)
        gpg_path_layout.addWidget(gpg_key_browse)
        gpg_form.addRow("Key File:", gpg_path_layout)

        self.gpg_passphrase = QLineEdit()
        self.gpg_passphrase.setEchoMode(QLineEdit.Password)
        self.gpg_passphrase.setPlaceholderText("(optional)")
        gpg_form.addRow("Passphrase:", self.gpg_passphrase)

        left_layout.addWidget(gpg_group)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        init_btn = QPushButton("Initialize Repository")
        init_btn.clicked.connect(self._init_repo)
        actions.addWidget(init_btn)

        add_pkg_btn = QPushButton("Add Package...")
        add_pkg_btn.clicked.connect(self._add_package)
        actions.addWidget(add_pkg_btn)

        gen_meta_btn = QPushButton("Generate Metadata")
        gen_meta_btn.clicked.connect(self._generate_metadata)
        actions.addWidget(gen_meta_btn)

        actions.addStretch()
        left_layout.addLayout(actions)

        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(QLabel("<b>Repository Packages</b>"))

        self.pkg_table = QTableWidget()
        self.pkg_table.setColumnCount(4)
        self.pkg_table.setHorizontalHeaderLabels(["Package", "Version", "Architecture", "Size"])
        self.pkg_table.horizontalHeader().setStretchLastSection(True)
        self.pkg_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.pkg_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.pkg_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.pkg_table.setStyleSheet("""
            QTableWidget {
                background: #181825;
                border: 1px solid #313244;
                border-radius: 6px;
                gridline-color: #313244;
            }
            QTableWidget::item { padding: 6px; color: #cdd6f4; }
            QTableWidget::item:selected { background: #45475a; }
            QHeaderView::section {
                background: #11111b;
                color: #a6adc8;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #313244;
                font-weight: bold;
            }
        """)
        right_layout.addWidget(self.pkg_table, 1)

        right_layout.addWidget(QLabel("<b>Output / Log</b>"))
        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        self.output_log.setMaximumHeight(150)
        self.output_log.setStyleSheet("""
            QTextEdit {
                background: #11111b;
                color: #cdd6f4;
                font-family: "JetBrains Mono", "Fira Code", monospace;
                font-size: 12px;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        right_layout.addWidget(self.output_log)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

    def _log(self, msg: str):
        self.output_log.append(msg)

    def _browse_repo_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Repository Directory")
        if path:
            self.repo_path.setText(path)

    def _browse_gpg_key(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select GPG Key", filter="All Files (*)")
        if path:
            self.gpg_file.setText(path)

    def _init_repo(self):
        repo_dir = self.repo_path.text().strip()
        suite = self.repo_suite.currentText()
        component = self.repo_component.currentText()
        arch = "binary-amd64"

        if not repo_dir:
            QMessageBox.warning(self, "Repository Error", "Repository path is required.")
            return

        base = Path(repo_dir)
        packages_dir = base / "dists" / suite / component / arch
        pool_dir = base / "pool" / component

        try:
            packages_dir.mkdir(parents=True, exist_ok=True)
            pool_dir.mkdir(parents=True, exist_ok=True)
            self._log(f"Repository initialized at {base}")
            self._log(f"Suite: {suite}, Component: {component}")
            QMessageBox.information(self, "Repository", f"Repository initialized at {repo_dir}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create repository: {e}")

    def _add_package(self):
        repo_dir = self.repo_path.text().strip()
        if not repo_dir:
            QMessageBox.warning(self, "Repository Error", "Please initialize a repository first.")
            return

        paths, _ = QFileDialog.getOpenFileNames(self, "Select .deb Packages", filter="Debian Packages (*.deb)")
        if not paths:
            return

        component = self.repo_component.currentText()
        pool_dir = Path(repo_dir) / "pool" / component

        for src_path in paths:
            p = Path(src_path)
            target = pool_dir / p.name
            try:
                shutil.copy2(str(p), str(target))
                self._log(f"Added: {p.name}")
                # Get package info
                result = run_command(["dpkg-deb", "--info", str(target)])
                if result[0] == 0:
                    info = result[1]
                    pkg_name = "?"
                    version = "?"
                    arch = "?"
                    for line in info.split("\n"):
                        if line.startswith(" Package:"):
                            pkg_name = line.split(":", 1)[1].strip()
                        elif line.startswith(" Version:"):
                            version = line.split(":", 1)[1].strip()
                        elif line.startswith(" Architecture:"):
                            arch = line.split(":", 1)[1].strip()
                    row = self.pkg_table.rowCount()
                    self.pkg_table.insertRow(row)
                    self.pkg_table.setItem(row, 0, QTableWidgetItem(pkg_name))
                    self.pkg_table.setItem(row, 1, QTableWidgetItem(version))
                    self.pkg_table.setItem(row, 2, QTableWidgetItem(arch))
                    self.pkg_table.setItem(row, 3, QTableWidgetItem(f"{p.stat().st_size / 1024:.1f} KB"))
            except Exception as e:
                self._log(f"Error adding {p.name}: {e}")

        self._log(f"Added {len(paths)} package(s)")

    def _generate_metadata(self):
        repo_dir = self.repo_path.text().strip()
        if not repo_dir:
            QMessageBox.warning(self, "Repository Error", "Repository path is required.")
            return

        base = Path(repo_dir)
        suite = self.repo_suite.currentText()
        component = self.repo_component.currentText()
        arch = "binary-amd64"
        packages_dir = base / "dists" / suite / component / arch
        pool_dir = base / "pool" / component

        if not packages_dir.exists():
            packages_dir.mkdir(parents=True, exist_ok=True)

        self._log("Generating Packages.gz...")
        try:
            # Find all .deb files and generate Packages
            debs = list(pool_dir.glob("*.deb"))
            if not debs:
                self._log("No packages found in pool.")
                return

            packages_file = packages_dir / "Packages"
            with open(packages_file, "w") as f:
                for deb_path in debs:
                    result = run_command(["dpkg-deb", "--info", str(deb_path)])
                    if result[0] == 0:
                        f.write(result[1])
                        f.write(f"Filename: pool/{component}/{deb_path.name}\n")
                        f.write(f"Size: {deb_path.stat().st_size}\n")
                        f.write(f"SHA256: {self._sha256(deb_path)}\n")
                        f.write("\n")

            # Generate Packages.gz
            import gzip
            with open(packages_file, "rb") as f_in:
                with gzip.open(f"{packages_file}.gz", "wb") as f_out:
                    f_out.writelines(f_in)

            self._log(f"Generated: {packages_file} ({len(debs)} packages)")

            # Generate Release if GPG key available
            release_dir = base / "dists" / suite
            release_file = release_dir / "Release"

            origin = self.repo_origin.text().strip() or self.repo_name.text().strip() or "Boss Package Manager"
            label = self.repo_label.text().strip() or origin

            release_content = (
                f"Origin: {origin}\n"
                f"Label: {label}\n"
                f"Suite: {suite}\n"
                f"Codename: {suite}\n"
                f"Architectures: {arch.split('-')[1]}\n"
                f"Components: {component}\n"
                f"Description: {self.repo_desc.text().strip() or 'APT Repository'}\n"
            )
            release_dir.mkdir(parents=True, exist_ok=True)
            release_file.write_text(release_content)
            self._log(f"Generated: {release_file}")

            # GPG sign Release
            gpg_key = self.gpg_key.text().strip()
            gpg_file = self.gpg_file.text().strip()
            if gpg_key or gpg_file:
                self._sign_release(release_file, gpg_key, gpg_file)

            QMessageBox.information(self, "Repository", "Metadata generated successfully!")
        except Exception as e:
            self._log(f"Error: {e}")
            QMessageBox.critical(self, "Error", f"Metadata generation failed: {e}")

    def _sign_release(self, release_file: Path, key_id: str, key_file: str):
        self._log("Signing Release file with GPG...")
        try:
            if key_file:
                result = run_command(
                    ["gpg", "--import", key_file]
                )
                if result[0] != 0:
                    self._log(f"GPG import warning: {result[2]}")

            cmd = ["gpg", "--detach-sign", "--armor", "-o", str(release_file) + ".gpg"]
            if key_id:
                cmd.extend(["--local-user", key_id])

            cmd.append(str(release_file))
            result = run_command(cmd)
            if result[0] == 0:
                self._log("Release signed successfully!")
            else:
                self._log(f"GPG signing failed: {result[2]}")

            # Also create InRelease
            result = run_command([
                "gpg", "--clearsign", "--armor",
                "-o", str(release_file.parent / "InRelease"),
            ] + (["--local-user", key_id] if key_id else []) + [str(release_file)])
            if result[0] == 0:
                self._log("InRelease generated.")
        except Exception as e:
            self._log(f"GPG signing error: {e}")

    def _sha256(self, path: Path) -> str:
        import hashlib
        h = hashlib.sha256()
        h.update(path.read_bytes())
        return h.hexdigest()
