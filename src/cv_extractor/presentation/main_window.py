"""Main window and drag/drop behaviors for the PyQt UI."""

from __future__ import annotations

import traceback
from pathlib import Path

from PyQt6.QtCore import QObject, QThread, Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QFontDatabase
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cv_extractor.presentation.viewmodel import ExtractionResult, ExtractionViewModel
from cv_extractor.presentation.widgets import DropZoneWidget


class ExtractionWorker(QObject):
    """Background worker to keep the UI responsive while extracting."""

    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str, str)
    finished = pyqtSignal()

    def __init__(self, view_model: ExtractionViewModel, input_path: Path) -> None:
        super().__init__()
        self._view_model = view_model
        self._input_path = input_path

    def run(self) -> None:
        try:
            result = self._view_model.extract(self._input_path)
            self.succeeded.emit(result)
        except Exception as exc:  # pragma: no cover - UI runtime behavior
            self.failed.emit(str(exc), traceback.format_exc())
        finally:
            self.finished.emit()


class MainWindow(QMainWindow):
    """Minimal desktop UI for CV extraction."""

    def __init__(self, view_model: ExtractionViewModel | None = None) -> None:
        super().__init__()
        self._view_model = view_model or ExtractionViewModel()
        self._selected_file: Path | None = None
        self._thread: QThread | None = None
        self._worker: ExtractionWorker | None = None

        self.setWindowTitle("CV Extractor")
        self.resize(960, 700)
        self.setAcceptDrops(True)
        self._build_ui()

    def _build_ui(self) -> None:
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        controls_layout = QHBoxLayout()
        self._open_button = QPushButton("Open...")
        self._open_button.clicked.connect(self._open_file_dialog)
        self._extract_button = QPushButton("Extract")
        self._extract_button.setEnabled(False)
        self._extract_button.clicked.connect(self._extract_selected_file)
        self._file_label = QLabel("No file selected.")
        self._file_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._file_label.setWordWrap(True)

        controls_layout.addWidget(self._open_button)
        controls_layout.addWidget(self._extract_button)
        controls_layout.addWidget(self._file_label, stretch=1)
        main_layout.addLayout(controls_layout)

        self._drop_zone = DropZoneWidget()
        self._drop_zone.clicked.connect(self._open_file_dialog)
        main_layout.addWidget(self._drop_zone)

        self._status_label = QLabel("Status: Idle")
        main_layout.addWidget(self._status_label)

        self._json_view = QPlainTextEdit()
        self._json_view.setReadOnly(True)
        fixed_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        self._json_view.setFont(fixed_font)
        self._json_view.setPlaceholderText("Extracted JSON will appear here.")
        main_layout.addWidget(self._json_view, stretch=1)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def _open_file_dialog(self) -> None:
        selected_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CV File",
            str(Path.cwd()),
            "CV Files (*.pdf *.docx *.txt);;All Files (*)",
        )
        if not selected_path:
            return
        self._set_selected_file(Path(selected_path))

    def _set_selected_file(self, file_path: Path) -> None:
        if not self._view_model.is_supported_file(file_path):
            self._show_error_dialog(
                "Unsupported file type.",
                f"Supported types: {self._view_model.supported_extensions_label()}",
            )
            return

        self._selected_file = file_path
        self._file_label.setText(str(file_path))
        if self._thread is None:
            self._extract_button.setEnabled(True)
        self._status_label.setText("Status: Ready")

    def _extract_selected_file(self) -> None:
        if self._selected_file is None:
            self._show_error_dialog("No file selected.", "Choose or drop a CV file first.")
            return
        self._run_extraction(self._selected_file)

    def _run_extraction(self, file_path: Path) -> None:
        if self._thread is not None:
            return

        self._set_busy_state(True)
        self._status_label.setText(f"Status: Extracting {file_path.name} ...")
        self._thread = QThread(self)
        self._worker = ExtractionWorker(self._view_model, file_path)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.succeeded.connect(self._on_extraction_success)
        self._worker.failed.connect(self._on_extraction_failure)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._on_worker_finished)
        self._thread.start()

    def _on_extraction_success(self, result: object) -> None:
        extraction_result = result
        if not isinstance(extraction_result, ExtractionResult):
            self._on_extraction_failure("Unexpected worker payload.", "Worker returned invalid data.")
            return
        self._json_view.setPlainText(extraction_result.pretty_json)
        self._status_label.setText(f"Status: Saved to {extraction_result.output_path}")

    def _on_extraction_failure(self, message: str, details: str) -> None:
        self._json_view.clear()
        self._status_label.setText("Status: Failed")
        self._show_error_dialog("Extraction failed.", message, details)

    def _on_worker_finished(self) -> None:
        self._thread = None
        self._worker = None
        self._set_busy_state(False)
        if self._selected_file is None:
            self._extract_button.setEnabled(False)

    def _set_busy_state(self, is_busy: bool) -> None:
        self._open_button.setEnabled(not is_busy)
        self._extract_button.setEnabled((not is_busy) and self._selected_file is not None)

    def _show_error_dialog(self, title: str, message: str, details: str = "") -> None:
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Critical)
        dialog.setWindowTitle("CV Extractor Error")
        dialog.setText(title)
        dialog.setInformativeText(message)
        if details:
            dialog.setDetailedText(details)
        dialog.exec()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # type: ignore[override]
        path = self._extract_supported_path_from_drop(event)
        if path is None:
            self._drop_zone.set_drag_active(False)
            event.ignore()
            return
        self._drop_zone.set_drag_active(True)
        event.acceptProposedAction()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:  # type: ignore[override]
        self._drop_zone.set_drag_active(False)
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:  # type: ignore[override]
        self._drop_zone.set_drag_active(False)
        path = self._extract_supported_path_from_drop(event)
        if path is None:
            event.ignore()
            return

        event.acceptProposedAction()
        self._set_selected_file(path)
        self._run_extraction(path)

    def _extract_supported_path_from_drop(self, event: QDragEnterEvent | QDropEvent) -> Path | None:
        mime_data = event.mimeData()
        if not mime_data.hasUrls():
            return None

        for url in mime_data.urls():
            if not url.isLocalFile():
                continue
            candidate = Path(url.toLocalFile())
            if self._view_model.is_supported_file(candidate):
                return candidate
        return None

