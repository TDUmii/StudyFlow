"""StudyFlow Simple — bản tối giản dùng để dạy Python và PySide6."""

import sys
from datetime import date
from pathlib import Path

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from teaching.csv_helper import ensure_csv, next_id, read_csv, write_csv
from teaching.translations import SUBJECT_LIBRARY, library_subject, translate

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SUBJECT_FILE = DATA_DIR / "subjects.csv"
TASK_FILE = DATA_DIR / "tasks.csv"
SETTING_FILE = DATA_DIR / "settings.csv"

SUBJECT_FIELDS = ["id", "key", "name_en", "name_vi"]
TASK_FIELDS = ["id", "title", "subject_id", "deadline", "status"]
SETTING_FIELDS = ["key", "value"]


STYLE = """
QMainWindow, QWidget { background: #F7F8FA; font-family: "Segoe UI"; font-size: 14px; }
QTabWidget::pane { border: 1px solid #E4E4E7; background: white; }
QTabBar::tab { background: #F4F4F5; border: 1px solid #E4E4E7; border-bottom: 0; padding: 10px 20px; margin-right: 3px; }
QTabBar::tab:selected { background: white; color: #4F46E5; font-weight: 700; }
QLineEdit, QComboBox, QDateEdit { background: white; padding: 7px; border: 1px solid #D4D4D8; border-radius: 6px; }
QPushButton { background: white; padding: 8px 14px; border: 1px solid #D4D4D8; border-radius: 6px; }
QPushButton:hover { border-color: #6366F1; }
QPushButton#primary { background: #6366F1; color: white; border-color: #6366F1; }
QTableWidget { background: white; border: 1px solid #E4E4E7; gridline-color: #F4F4F5; selection-background-color: #EEF2FF; selection-color: #18181B; outline: 0; }
QTableWidget::item { padding: 6px; }
QTableWidget::item:focus { outline: none; }
QHeaderView::section { background: #F4F4F5; padding: 7px; border: 0; font-weight: 600; }
QLabel#title { font-size: 25px; font-weight: 700; color: #4F46E5; }
QLabel#number { font-size: 24px; font-weight: 700; }
QWidget#card { background: white; border: 1px solid #E4E4E7; border-radius: 9px; }
QWidget#card QLabel { background: transparent; border: 0; }
"""


class StudyFlowSimple(QMainWindow):
    def __init__(self):
        super().__init__()
        ensure_csv(SUBJECT_FILE, SUBJECT_FIELDS)
        ensure_csv(TASK_FILE, TASK_FIELDS)
        ensure_csv(SETTING_FILE, SETTING_FIELDS)

        self.language = self.load_language()
        self.resize(1050, 680)
        self.setMinimumSize(850, 560)
        self.build_ui()

    def text(self, key, **values):
        return translate(self.language, key, **values)

    def load_language(self):
        settings = read_csv(SETTING_FILE, SETTING_FIELDS)
        for setting in settings:
            if setting["key"] == "language" and setting["value"] in ("en", "vi"):
                return setting["value"]
        return "vi"

    def save_language(self, language):
        rows = [{"key": "language", "value": language}]
        write_csv(SETTING_FILE, SETTING_FIELDS, rows)

    def build_ui(self):
        self.setWindowTitle(self.text("window"))
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 18, 24, 24)
        layout.setSpacing(14)

        top_bar = QHBoxLayout()
        title = QLabel("StudyFlow Simple")
        title.setObjectName("title")
        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(QLabel(self.text("language")))

        language_box = QComboBox()
        language_box.addItem("English", "en")
        language_box.addItem("Tiếng Việt", "vi")
        language_box.setCurrentIndex(language_box.findData(self.language))
        language_box.currentIndexChanged.connect(
            lambda: self.change_language(language_box.currentData())
        )
        top_bar.addWidget(language_box)
        layout.addLayout(top_bar)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.make_dashboard(), self.text("dashboard"))
        self.tabs.addTab(self.make_subject_page(), self.text("subjects"))
        self.tabs.addTab(self.make_task_page(), self.text("tasks"))
        layout.addWidget(self.tabs)

        self.refresh_all()

    def change_language(self, language):
        if language == self.language:
            return
        current_tab = self.tabs.currentIndex()
        self.language = language
        self.save_language(language)
        self.build_ui()
        self.tabs.setCurrentIndex(current_tab)

    def make_dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        cards = QHBoxLayout()
        self.subject_count = self.make_number_card(cards, self.text("subject_count"))
        self.pending_count = self.make_number_card(cards, self.text("pending_count"))
        self.today_count = self.make_number_card(cards, self.text("today_count"))
        layout.addLayout(cards)

        layout.addWidget(QLabel(self.text("recommendation")))
        self.recommendation = QLabel()
        self.recommendation.setWordWrap(True)
        self.recommendation.setStyleSheet(
            "background: white; border: 1px solid #E4E4E7; padding: 18px;"
        )
        layout.addWidget(self.recommendation)
        layout.addStretch()
        return page

    def make_number_card(self, parent_layout, title):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.addWidget(QLabel(title))
        number = QLabel("0")
        number.setObjectName("number")
        layout.addWidget(number)
        parent_layout.addWidget(card)
        return number

    def make_subject_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        self.subject_library = QComboBox()
        self.subject_library.addItem(self.text("custom_subject"), "")
        for subject in SUBJECT_LIBRARY:
            self.subject_library.addItem(subject[self.language], subject["key"])
        self.subject_library.currentIndexChanged.connect(self.update_custom_fields)

        self.subject_name_en = QLineEdit()
        self.subject_name_vi = QLineEdit()
        form.addRow(self.text("subject_library"), self.subject_library)
        form.addRow(self.text("name_en"), self.subject_name_en)
        form.addRow(self.text("name_vi"), self.subject_name_vi)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        add_button = QPushButton(self.text("add_subject"))
        add_button.setObjectName("primary")
        add_button.clicked.connect(self.add_subject)
        delete_button = QPushButton(self.text("delete_subject"))
        delete_button.clicked.connect(self.delete_subject)
        buttons.addWidget(add_button)
        buttons.addWidget(delete_button)
        buttons.addStretch()
        layout.addLayout(buttons)

        self.subject_table = self.make_table([self.text("id"), self.text("name")])
        layout.addWidget(self.subject_table)
        self.update_custom_fields()
        return page

    def make_task_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        self.task_title = QLineEdit()
        self.task_subject = QComboBox()
        self.task_deadline = QDateEdit()
        self.task_deadline.setCalendarPopup(True)
        self.task_deadline.setDate(QDate.currentDate())
        self.task_deadline.setDisplayFormat("dd/MM/yyyy")
        form.addRow(self.text("task_title"), self.task_title)
        form.addRow(self.text("subject"), self.task_subject)
        form.addRow(self.text("deadline"), self.task_deadline)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        for label, action, primary in (
            (self.text("add_task"), self.add_task, True),
            (self.text("complete_task"), self.complete_task, False),
            (self.text("delete_task"), self.delete_task, False),
        ):
            button = QPushButton(label)
            if primary:
                button.setObjectName("primary")
            button.clicked.connect(action)
            buttons.addWidget(button)
        buttons.addStretch()
        layout.addLayout(buttons)

        headers = [
            self.text("id"),
            self.text("title"),
            self.text("subject"),
            self.text("deadline"),
            self.text("status"),
        ]
        self.task_table = self.make_table(headers)
        layout.addWidget(self.task_table)
        return page

    def make_table(self, headers):
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        return table

    def update_custom_fields(self):
        custom = self.subject_library.currentData() == ""
        self.subject_name_en.setEnabled(custom)
        self.subject_name_vi.setEnabled(custom)

    def subject_display_name(self, subject):
        if subject["key"]:
            library_item = library_subject(subject["key"])
            if library_item:
                return library_item[self.language]
        return subject["name_vi"] if self.language == "vi" else subject["name_en"]

    def add_subject(self):
        subjects = read_csv(SUBJECT_FILE, SUBJECT_FIELDS)
        key = self.subject_library.currentData()

        if key:
            library_item = library_subject(key)
            name_en = library_item["en"]
            name_vi = library_item["vi"]
        else:
            name_en = self.subject_name_en.text().strip()
            name_vi = self.subject_name_vi.text().strip()
            if not name_en or not name_vi:
                self.warn("fill_names")
                return

        for subject in subjects:
            same_key = key and subject["key"] == key
            same_name = subject["name_en"].casefold() == name_en.casefold()
            if same_key or same_name:
                self.warn("subject_exists")
                return

        subjects.append(
            {
                "id": str(next_id(subjects)),
                "key": key,
                "name_en": name_en,
                "name_vi": name_vi,
            }
        )
        write_csv(SUBJECT_FILE, SUBJECT_FIELDS, subjects)
        self.subject_name_en.clear()
        self.subject_name_vi.clear()
        self.refresh_all()

    def delete_subject(self):
        subject_id = self.selected_id(self.subject_table)
        if not subject_id:
            self.warn("select_row")
            return

        tasks = read_csv(TASK_FILE, TASK_FIELDS)
        for task in tasks:
            if task["subject_id"] == subject_id:
                self.warn("subject_in_use")
                return

        subjects = read_csv(SUBJECT_FILE, SUBJECT_FIELDS)
        subjects = [subject for subject in subjects if subject["id"] != subject_id]
        write_csv(SUBJECT_FILE, SUBJECT_FIELDS, subjects)
        self.refresh_all()

    def add_task(self):
        title = self.task_title.text().strip()
        subject_id = self.task_subject.currentData()
        if not title:
            self.warn("enter_title")
            return
        if not subject_id:
            self.warn("select_subject")
            return

        tasks = read_csv(TASK_FILE, TASK_FIELDS)
        tasks.append(
            {
                "id": str(next_id(tasks)),
                "title": title,
                "subject_id": subject_id,
                "deadline": self.task_deadline.date().toString("yyyy-MM-dd"),
                "status": "TODO",
            }
        )
        write_csv(TASK_FILE, TASK_FIELDS, tasks)
        self.task_title.clear()
        self.refresh_all()

    def complete_task(self):
        task_id = self.selected_id(self.task_table)
        if not task_id:
            self.warn("select_row")
            return

        tasks = read_csv(TASK_FILE, TASK_FIELDS)
        for task in tasks:
            if task["id"] == task_id:
                task["status"] = "COMPLETED"
        write_csv(TASK_FILE, TASK_FIELDS, tasks)
        self.refresh_all()

    def delete_task(self):
        task_id = self.selected_id(self.task_table)
        if not task_id:
            self.warn("select_row")
            return

        tasks = read_csv(TASK_FILE, TASK_FIELDS)
        tasks = [task for task in tasks if task["id"] != task_id]
        write_csv(TASK_FILE, TASK_FIELDS, tasks)
        self.refresh_all()

    def refresh_all(self):
        subjects = read_csv(SUBJECT_FILE, SUBJECT_FIELDS)
        tasks = read_csv(TASK_FILE, TASK_FIELDS)
        subject_names = {}
        for subject in subjects:
            subject_names[subject["id"]] = self.subject_display_name(subject)

        self.subject_table.setRowCount(0)
        for subject in subjects:
            self.add_table_row(
                self.subject_table,
                [subject["id"], self.subject_display_name(subject)],
            )

        selected_subject = self.task_subject.currentData()
        self.task_subject.clear()
        for subject in subjects:
            self.task_subject.addItem(self.subject_display_name(subject), subject["id"])
        old_index = self.task_subject.findData(selected_subject)
        if old_index >= 0:
            self.task_subject.setCurrentIndex(old_index)

        self.task_table.setRowCount(0)
        for task in tasks:
            status_key = "completed" if task["status"] == "COMPLETED" else "todo"
            self.add_table_row(
                self.task_table,
                [
                    task["id"],
                    task["title"],
                    subject_names.get(task["subject_id"], "—"),
                    task["deadline"],
                    self.text(status_key),
                ],
            )

        pending = [task for task in tasks if task["status"] != "COMPLETED"]
        today = date.today().isoformat()
        self.subject_count.setText(str(len(subjects)))
        self.pending_count.setText(str(len(pending)))
        self.today_count.setText(
            str(sum(task["deadline"] == today for task in pending))
        )
        self.recommendation.setText(self.make_recommendation(pending, subject_names))

    def make_recommendation(self, pending_tasks, subject_names):
        if not pending_tasks:
            return self.text("no_tasks")
        pending_tasks.sort(key=lambda task: task["deadline"])
        task = pending_tasks[0]
        return self.text(
            "study_today",
            subject=subject_names.get(task["subject_id"], "—"),
            task=task["title"],
            deadline=task["deadline"],
        )

    def add_table_row(self, table, values):
        row = table.rowCount()
        table.insertRow(row)
        for column, value in enumerate(values):
            table.setItem(row, column, QTableWidgetItem(str(value)))

    def selected_id(self, table):
        selected = table.selectedItems()
        return selected[0].text() if selected else ""

    def warn(self, key):
        QMessageBox.warning(self, self.text("message"), self.text(key))


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    window = StudyFlowSimple()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
