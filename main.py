from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from app.services import AppService
from app.ui.dialogs import OnboardingDialog
from app.ui.main_window import MainWindow

ROOT = Path(__file__).resolve().parent


def configure_logging() -> None:
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(
        filename=ROOT / "logs" / "studyflow.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )


def create_application() -> tuple[QApplication, MainWindow | None]:
    configure_logging()
    logging.info("StudyFlow startup")
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("StudyFlow")
    app.setOrganizationName("StudyFlow")
    try:
        style_path = ROOT / "app" / "theme" / "style.qss"
        app.setStyleSheet(style_path.read_text(encoding="utf-8"))
        service = AppService(ROOT / "data", ROOT / "exports")
        if not service.repos.profile.get_name():
            onboarding = OnboardingDialog()
            if onboarding.exec() != QDialog.Accepted:
                return app, None
            service.setup_profile(*onboarding.values())
        window = MainWindow(service)
        return app, window
    except Exception as exc:
        logging.exception("Application startup failed")
        QMessageBox.critical(
            None,
            "StudyFlow could not start",
            f"StudyFlow could not prepare its local files.\n\n{exc}",
        )
        return app, None


def main() -> int:
    app, window = create_application()
    if window is None:
        return 0
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
