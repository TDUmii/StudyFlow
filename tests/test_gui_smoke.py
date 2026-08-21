import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow


def test_table_selection_has_explicit_readable_colors():
    stylesheet = Path("app/theme/style.qss").read_text(encoding="utf-8")
    assert "selection-background-color: #EEF2FF" in stylesheet
    assert "selection-color: #18181B" in stylesheet
    assert "QTableWidget::item:selected" in stylesheet


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
