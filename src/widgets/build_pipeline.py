from __future__ import annotations
from datetime import datetime
from pathlib import Path
from threading import Thread

from PySide6.QtCore import Qt, Signal, QObject, QProcess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QPlainTextEdit, QSplitter, QMessageBox,
    QAbstractItemView, QComboBox,
)
from PySide6.QtGui import QColor, QTextCursor, QTextCharFormat

from src.models.build import BuildRecord, BuildStatus, BuildLog
from src.models.package import PackageConfig


class BuildSignals(QObject):
    progress_updated = Signal(int, str)
    log_added = Signal(object)
    build_complete = Signal(object)


class BuildPipelineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.build_records: list[BuildRecord] = []
        self.current_record: BuildRecord | None = None
        self._signals = BuildSignals()
        self._signals.progress_updated.connect(self._on_progress)
        self._signals.log_added.connect(self._on_log)
        self._signals.build_complete.connect(self._on_complete)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QVBoxLayout()
        title = QLabel("Build Pipeline")
        title.setObjectName("section-title")
        desc = QLabel("Build, monitor, and manage Debian package builds with real-time progress")
        desc.setObjectName("section-desc")
        header.addWidget(title)
        header.addWidget(desc)
        layout.addLayout(header)

        controls = QHBoxLayout()
        controls.setSpacing(8)

        self.build_btn = QPushButton("🔨 Build Package")
        self.build_btn.setStyleSheet("""
            QPushButton {
                background: #89b4fa;
                color: #1e1e2e;
                font-weight: bold;
                padding: 10px 24px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover { background: #74c7ec; }
            QPushButton:disabled { background: #45475a; color: #6c7086; }
        """)
        self.build_btn.clicked.connect(self._start_build)
        controls.addWidget(self.build_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_build)
        controls.addWidget(self.cancel_btn)

        self.install_btn = QPushButton("📥 Install")
        self.install_btn.setEnabled(False)
        self.install_btn.setStyleSheet("""
            QPushButton {
                background: #a6e3a1;
                color: #1e1e2e;
                font-weight: bold;
                padding: 10px 24px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover { background: #94e2d5; }
            QPushButton:disabled { background: #45475a; color: #6c7086; }
        """)
        self.install_btn.clicked.connect(self._install_package)
        controls.addWidget(self.install_btn)

        controls.addStretch()

        source_label = QLabel("Source:")
        controls.addWidget(source_label)
        self.source_combo = QComboBox()
        self.source_combo.addItem("Current Wizard Config", "wizard")
        self.source_combo.addItem("Last Successful Build", "last")
        controls.addWidget(self.source_combo)

        layout.addLayout(controls)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #313244;
                border-radius: 6px;
                text-align: center;
                height: 24px;
                background: #181825;
                color: #cdd6f4;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #89b4fa, stop:1 #a6e3a1);
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to build")
        self.status_label.setStyleSheet("color: #a6adc8; font-size: 13px;")
        layout.addWidget(self.status_label)

        splitter = QSplitter(Qt.Vertical)

        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.addWidget(QLabel("<b>Build Log</b>"))

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("""
            QPlainTextEdit {
                background: #11111b;
                color: #cdd6f4;
                font-family: "JetBrains Mono", "Fira Code", "Consolas", monospace;
                font-size: 12px;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        log_layout.addWidget(self.log_output)
        splitter.addWidget(log_widget)

        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        history_layout.setContentsMargins(0, 0, 0, 0)
        history_layout.addWidget(QLabel("<b>Build History</b>"))

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(["Time", "Package", "Version", "Arch", "Status", "Output"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.setStyleSheet("""
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
        history_layout.addWidget(self.history_table)
        splitter.addWidget(history_widget)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

    def _start_build(self):
        source = self.source_combo.currentData()
        config: PackageConfig | None = None

        if source == "wizard":
            if self.main_window and hasattr(self.main_window, 'pages'):
                wizard = self.main_window.pages[0]
                if isinstance(wizard, QWidget):
                    config = wizard.get_config() if hasattr(wizard, 'get_config') else None

        if not config or not config.package_name:
            QMessageBox.warning(self, "Build Error",
                                "No valid package configuration. Please configure a package in the Package Builder tab first.")
            return

        self.build_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_output.clear()
        self.status_label.setText("Building...")

        if self.main_window:
            self.main_window.status_message(f"Building {config.package_name} {config.version}...")

        from src.core.dpkg_builder import DPKGBuilder
        builder = DPKGBuilder(config)

        def build_thread():
            record = builder.build(
                progress_callback=lambda pct, msg: self._signals.progress_updated.emit(pct, msg),
                log_callback=lambda log: self._signals.log_added.emit(log),
            )
            self._signals.build_complete.emit(record)

        self._builder = builder
        thread = Thread(target=build_thread, daemon=True)
        thread.start()

    def _cancel_build(self):
        if hasattr(self, '_builder'):
            self._builder.cancel()
            self._add_log_entry(BuildLog(datetime.now(), "Cancelling build...", "warning"))

    def _install_package(self):
        if not hasattr(self, '_last_build_path') or not self._last_build_path:
            QMessageBox.warning(self, "Install Error", "No package to install. Build a package first.")
            return

        deb_path = self._last_build_path
        reply = QMessageBox.question(
            self, "Install Package",
            f"Install {Path(deb_path).name}?\n\nThis will run pkexec dpkg -i with administrator privileges.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self._add_log_entry(BuildLog(datetime.now(), f"Installing: {deb_path}", "info"))
        self.install_btn.setEnabled(False)
        self.status_label.setText("Installing package...")

        proc = QProcess(self)
        proc.readyReadStandardOutput.connect(lambda: self._on_install_output(proc))
        proc.readyReadStandardError.connect(lambda: self._on_install_output(proc))
        proc.finished.connect(lambda code: self._on_install_finished(code, proc))

        proc.start("pkexec", ["dpkg", "-i", deb_path])

    def _on_install_output(self, proc: QProcess):
        data = proc.readAll().data().decode("utf-8", errors="replace")
        for line in data.split("\n"):
            if line.strip():
                log = BuildLog(datetime.now(), line.strip(), "info")
                self._add_log_entry(log)

    def _on_install_finished(self, code: int, proc: QProcess):
        self._on_install_output(proc)
        stderr = proc.readAllStandardError().data().decode("utf-8", errors="replace")
        if stderr.strip():
            for line in stderr.split("\n"):
                if line.strip():
                    log = BuildLog(datetime.now(), line.strip(), "warning" if code != 0 else "info")
                    self._add_log_entry(log)

        if code == 0:
            self._add_log_entry(BuildLog(datetime.now(), "✅ Package installed successfully!", "success"))
            self.status_label.setText("✅ Package installed successfully")
        else:
            self._add_log_entry(BuildLog(datetime.now(), f"❌ Install failed (exit code {code})", "error"))
            self.status_label.setText("❌ Install failed")

        self.install_btn.setEnabled(True)

    def _on_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

    def _on_log(self, log_entry: BuildLog):
        self._add_log_entry(log_entry)

    def _add_log_entry(self, log_entry: BuildLog):
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.End)

        fmt = QTextCharFormat()
        if log_entry.level == "error":
            fmt.setForeground(QColor("#f38ba8"))
        elif log_entry.level == "warning":
            fmt.setForeground(QColor("#fab387"))
        elif log_entry.level == "success":
            fmt.setForeground(QColor("#a6e3a1"))
        else:
            fmt.setForeground(QColor("#cdd6f4"))

        cursor.insertText(str(log_entry) + "\n", fmt)
        self.log_output.setTextCursor(cursor)
        self.log_output.ensureCursorVisible()

    def _on_complete(self, record: BuildRecord):
        self.build_records.append(record)
        self.build_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self._add_history_row(record)

        if self.main_window:
            if record.status == BuildStatus.SUCCESS:
                self.main_window.status_message(f"Build successful: {record.output_path}", 10000)
            elif record.status == BuildStatus.FAILED:
                self.main_window.status_message(f"Build failed: {record.error_message}", 10000)
            else:
                self.main_window.status_message("Build cancelled", 5000)

        if record.status == BuildStatus.SUCCESS:
            self._last_build_path = record.output_path
            self.install_btn.setEnabled(True)
            self.status_label.setText(f"✅ Build complete: {record.output_path}")
            self.progress_bar.setStyleSheet(self.progress_bar.styleSheet().replace(
                "#89b4fa, stop:1 #a6e3a1", "#a6e3a1, stop:1 #a6e3a1"
            ))
        elif record.status == BuildStatus.FAILED:
            self.install_btn.setEnabled(False)
            self.status_label.setText(f"❌ Build failed: {record.error_message}")
        else:
            self.status_label.setText("⏹️ Build cancelled")

    def _add_history_row(self, record: BuildRecord):
        row = self.history_table.rowCount()
        self.history_table.insertRow(row)

        time_str = record.started_at.strftime("%H:%M:%S") if record.started_at else "-"
        self.history_table.setItem(row, 0, QTableWidgetItem(time_str))
        self.history_table.setItem(row, 1, QTableWidgetItem(record.package_name))
        self.history_table.setItem(row, 2, QTableWidgetItem(record.version))
        self.history_table.setItem(row, 3, QTableWidgetItem(record.architecture))

        status_item = QTableWidgetItem(record.status.value)
        color_map = {
            BuildStatus.SUCCESS: QColor("#a6e3a1"),
            BuildStatus.FAILED: QColor("#f38ba8"),
            BuildStatus.RUNNING: QColor("#89b4fa"),
            BuildStatus.QUEUED: QColor("#fab387"),
            BuildStatus.CANCELLED: QColor("#6c7086"),
        }
        status_item.setForeground(color_map.get(record.status, QColor("#cdd6f4")))
        self.history_table.setItem(row, 4, status_item)

        output = record.output_path or record.error_message or "-"
        self.history_table.setItem(row, 5, QTableWidgetItem(output))
        self.history_table.resizeRowToContents(row)
