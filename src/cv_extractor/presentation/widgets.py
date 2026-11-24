"""Reusable UI widgets for the PyQt presentation layer."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout


class DropZoneWidget(QFrame):
    """Clickable visual drop zone for CV files."""

    clicked = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dropZone")
        self.setMinimumHeight(140)
        self._label = QLabel(
            "Drop a CV file here\nSupported: .pdf, .docx, .txt\n(or click Open...)"
        )
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self._label)
        self.setLayout(layout)

        self.set_drag_active(False)

    def set_drag_active(self, is_active: bool) -> None:
        if is_active:
            self.setStyleSheet(
                "QFrame#dropZone { border: 2px dashed #2f6fda; border-radius: 8px; background: #eef4ff; }"
            )
            return
        self.setStyleSheet(
            "QFrame#dropZone { border: 2px dashed #999; border-radius: 8px; background: #f7f7f7; }"
        )

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

