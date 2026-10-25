from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("XXBeadPattern")

    try:
        window = MainWindow()
    except Exception as exc:
        QMessageBox.critical(
            None,
            "XXBeadPattern 启动失败",
            str(exc),
        )
        return 1

    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())