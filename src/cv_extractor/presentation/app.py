"""PyQt application bootstrap entry point."""

from __future__ import annotations

import logging
import sys

from PyQt6.QtWidgets import QApplication

from cv_extractor.presentation.main_window import MainWindow


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

