from __future__ import annotations

import sys

from PySide6.QtCore import QSettings

from core.i18n import translate, translate_error
from PySide6.QtWidgets import QApplication, QMessageBox

from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("XXBeadPattern")

    settings = QSettings("XXBeadPattern", "XXBeadPattern")
    language = settings.value("language", "zh")
    language = language if language in {"zh", "en"} else "zh"

    try:
        window = MainWindow(language=language, settings=settings)
    except Exception as exc:
        QMessageBox.critical(
            None,
            translate(language, "XXBeadPattern 启动失败"),
            translate_error(language, str(exc)),
        )
        return 1

    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())