import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow


def test_main_window_and_all_navigation(service):
    app = QApplication.instance() or QApplication([])
    window = MainWindow(service)
    assert window.stack.count() == 10
    for index in range(window.stack.count()):
        window.show_page(index)
        app.processEvents()
    window.resize(1100, 700)
    app.processEvents()
    window.close()
