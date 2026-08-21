from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from app.i18n import language_manager, tr
from app.ui.pages import (
    AssistantPage,
    DashboardPage,
    FlashcardsPage,
    NotesPage,
    PlannerPage,
    QuizPage,
    SettingsPage,
    StatisticsPage,
    SubjectsPage,
    TasksPage,
)


class MainWindow(QMainWindow):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self.resize(1400, 850)
        self.setMinimumSize(1100, 700)
        language_manager.language_changed.connect(self.rebuild_for_language)
        self.build_ui()

    def build_ui(self, selected_index: int = 0):
        self.setWindowTitle(tr("app.window_title"))
        old_root = self.centralWidget()
        root = QWidget()
        root.setObjectName("AppRoot")
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(10, 0, 10, 12)
        side.setSpacing(4)
        self.brand = QLabel(tr("common.studyflow"))
        self.brand.setObjectName("Brand")
        side.addWidget(self.brand)
        self.stack = QStackedWidget()
        self.pages = []
        self.nav_buttons = []
        page_definitions = [
            ("nav.dashboard", DashboardPage, QStyle.SP_ComputerIcon),
            ("nav.planner", PlannerPage, QStyle.SP_FileDialogDetailedView),
            ("nav.subjects", SubjectsPage, QStyle.SP_DirIcon),
            ("nav.tasks", TasksPage, QStyle.SP_DialogApplyButton),
            ("nav.notes", NotesPage, QStyle.SP_FileIcon),
            ("nav.flashcards", FlashcardsPage, QStyle.SP_FileDialogListView),
            ("nav.quiz", QuizPage, QStyle.SP_DialogHelpButton),
            ("nav.statistics", StatisticsPage, QStyle.SP_ArrowUp),
            ("nav.assistant", AssistantPage, QStyle.SP_MessageBoxInformation),
        ]
        for index, (name_key, page_class, icon_type) in enumerate(page_definitions):
            page = page_class(self.service)
            page.changed.connect(self.refresh_all)
            self.pages.append(page)
            self.stack.addWidget(page)
            button = QPushButton(tr(name_key))
            button.setProperty("translationKey", name_key)
            button.setProperty("fullText", tr(name_key))
            button.setObjectName("Nav")
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setIcon(self.style().standardIcon(icon_type))
            button.clicked.connect(lambda checked, i=index: self.show_page(i))
            self.nav_buttons.append(button)
            side.addWidget(button)
        side.addStretch()
        settings = SettingsPage(self.service)
        settings.changed.connect(self.refresh_all)
        self.pages.append(settings)
        self.stack.addWidget(settings)
        button = QPushButton(tr("nav.settings"))
        button.setProperty("translationKey", "nav.settings")
        button.setProperty("fullText", tr("nav.settings"))
        button.setObjectName("Nav")
        button.setCheckable(True)
        button.setAutoExclusive(True)
        button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogContentsView))
        button.clicked.connect(lambda: self.show_page(len(self.pages) - 1))
        self.nav_buttons.append(button)
        side.addWidget(button)
        collapse = QPushButton(tr("nav.collapse"))
        collapse.clicked.connect(self.toggle_sidebar)
        side.addWidget(collapse)
        self.collapse_button = collapse
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)
        selected_index = min(selected_index, len(self.pages) - 1)
        self.nav_buttons[selected_index].setChecked(True)
        self.stack.setCurrentIndex(selected_index)
        self.refresh_all()
        if old_root is not None:
            old_root.deleteLater()

    def rebuild_for_language(self, _language_code: str):
        self.build_ui(self.stack.currentIndex())

    def show_page(self, index: int):
        self.stack.setCurrentIndex(index)
        self.pages[index].refresh()

    def refresh_all(self):
        for page in self.pages:
            try:
                page.refresh()
            except Exception as exc:
                # Keep one malformed data file from preventing other pages from refreshing.
                import logging

                logging.getLogger(__name__).exception("Page refresh failed: %s", exc)

    def toggle_sidebar(self):
        collapsed = self.sidebar.width() > 100
        self.sidebar.setFixedWidth(72 if collapsed else 220)
        self.brand.setText("SF" if collapsed else tr("common.studyflow"))
        self.collapse_button.setText(
            tr("nav.expand") if collapsed else tr("nav.collapse")
        )
        for button in self.nav_buttons:
            button.setText(
                "" if collapsed else button.property("fullText") or button.text()
            )
        if not collapsed:
            for button in self.nav_buttons:
                button.setText(tr(button.property("translationKey")))
