from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
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
        self.setWindowTitle("StudyFlow — Personal Study Assistant")
        self.resize(1400, 850)
        self.setMinimumSize(1100, 700)
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
        self.brand = QLabel("StudyFlow")
        self.brand.setObjectName("Brand")
        side.addWidget(self.brand)
        self.stack = QStackedWidget()
        self.pages = []
        self.nav_buttons = []
        page_definitions = [
            ("Dashboard", DashboardPage, QStyle.SP_ComputerIcon),
            ("Planner", PlannerPage, QStyle.SP_FileDialogDetailedView),
            ("Subjects", SubjectsPage, QStyle.SP_DirIcon),
            ("Tasks", TasksPage, QStyle.SP_DialogApplyButton),
            ("Notes", NotesPage, QStyle.SP_FileIcon),
            ("Flashcards", FlashcardsPage, QStyle.SP_FileDialogListView),
            ("Quiz", QuizPage, QStyle.SP_DialogHelpButton),
            ("Statistics", StatisticsPage, QStyle.SP_ArrowUp),
            ("Smart Assistant", AssistantPage, QStyle.SP_MessageBoxInformation),
        ]
        for index, (name, page_class, icon_type) in enumerate(page_definitions):
            page = page_class(service)
            page.changed.connect(self.refresh_all)
            self.pages.append(page)
            self.stack.addWidget(page)
            button = QPushButton(name)
            button.setObjectName("Nav")
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setIcon(self.style().standardIcon(icon_type))
            button.clicked.connect(lambda checked, i=index: self.show_page(i))
            self.nav_buttons.append(button)
            side.addWidget(button)
        side.addStretch()
        settings = SettingsPage(service)
        settings.changed.connect(self.refresh_all)
        self.pages.append(settings)
        self.stack.addWidget(settings)
        button = QPushButton("Settings")
        button.setObjectName("Nav")
        button.setCheckable(True)
        button.setAutoExclusive(True)
        button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogContentsView))
        button.clicked.connect(lambda: self.show_page(len(self.pages) - 1))
        self.nav_buttons.append(button)
        side.addWidget(button)
        collapse = QPushButton("Collapse sidebar")
        collapse.clicked.connect(self.toggle_sidebar)
        side.addWidget(collapse)
        self.collapse_button = collapse
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)
        self.nav_buttons[0].setChecked(True)
        self.refresh_all()

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
        self.brand.setText("SF" if collapsed else "StudyFlow")
        self.collapse_button.setText("Expand" if collapsed else "Collapse sidebar")
        for button in self.nav_buttons:
            button.setText(
                "" if collapsed else button.property("fullText") or button.text()
            )
        if not collapsed:
            names = [
                "Dashboard",
                "Planner",
                "Subjects",
                "Tasks",
                "Notes",
                "Flashcards",
                "Quiz",
                "Statistics",
                "Smart Assistant",
                "Settings",
            ]
            for button, name in zip(self.nav_buttons, names):
                button.setText(name)
