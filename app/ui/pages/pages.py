from __future__ import annotations

import os
from datetime import date

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.services import AssistantService, StatisticsService
from app.ui.dialogs import (
    FlashcardDialog,
    NoteDialog,
    QuizDialog,
    SessionDialog,
    SubjectDialog,
    TaskDialog,
)
from app.ui.widgets.common import card
from app.ui.widgets.charts import StudyCharts
from app.utils.dates import display_date
from app.utils.validators import ValidationError


def table(headers):
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.horizontalHeader().setStretchLastSection(True)
    widget.verticalHeader().setVisible(False)
    widget.setSelectionBehavior(QAbstractItemView.SelectRows)
    widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
    widget.setAlternatingRowColors(True)
    widget.setSortingEnabled(True)
    return widget


def fill_table(widget, rows):
    widget.setSortingEnabled(False)
    widget.setRowCount(0)
    for values in rows:
        row = widget.rowCount()
        widget.insertRow(row)
        for column, value in enumerate(values):
            widget.setItem(row, column, QTableWidgetItem(str(value)))
    widget.resizeColumnsToContents()
    widget.setSortingEnabled(True)


def selected_id(widget):
    items = widget.selectedItems()
    return int(items[0].data(Qt.UserRole) or items[0].text()) if items else None


class Page(QWidget):
    changed = Signal()

    def __init__(self, service, title, subtitle=""):
        super().__init__()
        self.service = service
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(28, 24, 28, 24)
        self.root.setSpacing(16)
        heading = QLabel(title)
        heading.setObjectName("PageTitle")
        self.root.addWidget(heading)
        if subtitle:
            description = QLabel(subtitle)
            description.setObjectName("Muted")
            self.root.addWidget(description)

    def refresh(self):
        pass

    def guard(self, action):
        try:
            return action()
        except (ValidationError, OSError) as exc:
            QMessageBox.warning(self, "StudyFlow", str(exc))


class DashboardPage(Page):
    def __init__(self, service):
        super().__init__(service, "Dashboard", "Your study day at a glance.")
        grid = QGridLayout()
        self.cards = {}
        for index, (key, label) in enumerate(
            (
                ("tasks_today", "Tasks Today"),
                ("study_minutes", "Study Time This Week"),
                ("upcoming", "Upcoming"),
                ("streak", "Current Streak"),
            )
        ):
            self.cards[key] = card(label)
            grid.addWidget(self.cards[key], 0, index)
        self.root.addLayout(grid)
        title = QLabel("Smart recommendation")
        title.setObjectName("SectionTitle")
        self.root.addWidget(title)
        self.recommendation = QLabel()
        self.recommendation.setWordWrap(True)
        self.recommendation.setObjectName("Card")
        self.recommendation.setStyleSheet("padding: 18px;")
        self.root.addWidget(self.recommendation)
        self.root.addStretch()

    def refresh(self):
        stats = StatisticsService(self.service.repos).summary()
        self.cards["tasks_today"].value_label.setText(str(stats["tasks_today"]))
        self.cards["study_minutes"].value_label.setText(f'{stats["study_minutes"]} min')
        self.cards["upcoming"].value_label.setText(str(stats["upcoming"]))
        self.cards["streak"].value_label.setText(f'{stats["streak"]} days')
        self.recommendation.setText(AssistantService(self.service.repos).message())


class SubjectsPage(Page):
    def __init__(self, service):
        super().__init__(service, "Subjects", "Organize learning goals by subject.")
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search subjects")
        self.search.textChanged.connect(self.refresh)
        add = QPushButton("Add Subject")
        add.setObjectName("Primary")
        add.clicked.connect(self.add)
        edit = QPushButton("Edit")
        edit.clicked.connect(self.edit)
        delete = QPushButton("Delete")
        delete.setObjectName("Danger")
        delete.clicked.connect(self.delete)
        [bar.addWidget(x) for x in (self.search, add, edit, delete)]
        self.root.addLayout(bar)
        self.table = table(["ID", "Name", "Target", "Description"])
        self.root.addWidget(self.table)

    def refresh(self):
        term = self.search.text().casefold()
        items = [
            s
            for s in self.service.repos.subjects.all()
            if term in (s.name + " " + s.description).casefold()
        ]
        fill_table(
            self.table,
            [(s.id, s.name, f"{s.target_score}%", s.description) for s in items],
        )

    def add(self):
        dialog = SubjectDialog(parent=self)
        if dialog.exec():
            self.guard(lambda: self.service.create_subject(**dialog.values()))
            self.changed.emit()

    def edit(self):
        item = self.service.repos.subjects.get(selected_id(self.table))
        if not item:
            return
        dialog = SubjectDialog(item, self)
        if dialog.exec():
            self.guard(lambda: self.service.update_subject(item.id, **dialog.values()))
            self.changed.emit()

    def delete(self):
        item = self.service.repos.subjects.get(selected_id(self.table))
        if (
            item
            and QMessageBox.question(
                self,
                "Delete subject",
                f'Delete "{item.name}"?\n\nThis action cannot be undone.',
            )
            == QMessageBox.Yes
        ):
            self.guard(lambda: self.service.delete_subject(item.id))
            self.changed.emit()


class TasksPage(Page):
    def __init__(self, service):
        super().__init__(
            service, "Tasks", "Search, filter, prioritize and complete your work."
        )
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search tasks")
        self.filter = QComboBox()
        self.filter.addItems(["ALL", "TODO", "IN_PROGRESS", "COMPLETED"])
        self.search.textChanged.connect(self.refresh)
        self.filter.currentTextChanged.connect(self.refresh)
        buttons = []
        for text, callback, name in (
            ("Add Task", self.add, "Primary"),
            ("Edit", self.edit, ""),
            ("Start", lambda: self.status("IN_PROGRESS"), ""),
            ("Complete", lambda: self.status("COMPLETED"), ""),
            ("Delete", self.delete, "Danger"),
        ):
            b = QPushButton(text)
            b.setObjectName(name)
            b.clicked.connect(callback)
            buttons.append(b)
        [bar.addWidget(x) for x in (self.search, self.filter, *buttons)]
        self.root.addLayout(bar)
        self.table = table(["ID", "Title", "Subject", "Deadline", "Priority", "Status"])
        self.root.addWidget(self.table)

    def refresh(self):
        names = {s.id: s.name for s in self.service.repos.subjects.all()}
        term = self.search.text().casefold()
        status = self.filter.currentText()
        items = [
            t
            for t in self.service.repos.tasks.all()
            if term in (t.title + " " + t.description).casefold()
            and (status == "ALL" or t.status == status)
        ]
        items.sort(
            key=lambda t: (
                t.deadline,
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(t.priority, 3),
            )
        )
        fill_table(
            self.table,
            [
                (
                    t.id,
                    t.title,
                    names.get(t.subject_id, "Missing subject"),
                    display_date(t.deadline),
                    t.priority,
                    t.status,
                )
                for t in items
            ],
        )

    def add(self):
        dialog = TaskDialog(self.service.repos.subjects.all(), parent=self)
        if dialog.exec():
            self.guard(lambda: self.service.create_task(**dialog.values()))
            self.changed.emit()

    def edit(self):
        item = self.service.repos.tasks.get(selected_id(self.table))
        if not item:
            return
        dialog = TaskDialog(self.service.repos.subjects.all(), item, self)
        if dialog.exec():
            self.guard(lambda: self.service.update_task(item.id, **dialog.values()))
            self.changed.emit()

    def status(self, status):
        item_id = selected_id(self.table)
        if item_id:
            self.guard(lambda: self.service.set_task_status(item_id, status))
            self.changed.emit()

    def delete(self):
        item = self.service.repos.tasks.get(selected_id(self.table))
        if (
            item
            and QMessageBox.question(self, "Delete task", f'Delete "{item.title}"?')
            == QMessageBox.Yes
        ):
            self.service.repos.tasks.delete(item.id)
            self.changed.emit()


class NotesPage(Page):
    def __init__(self, service):
        super().__init__(
            service,
            "Notes",
            "Plain-text notes safely stored with commas, quotes and new lines.",
        )
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search notes")
        self.search.textChanged.connect(self.refresh)
        add = QPushButton("Add Note")
        add.setObjectName("Primary")
        add.clicked.connect(self.add)
        edit = QPushButton("Edit")
        edit.clicked.connect(self.edit)
        delete = QPushButton("Delete")
        delete.setObjectName("Danger")
        delete.clicked.connect(self.delete)
        [bar.addWidget(x) for x in (self.search, add, edit, delete)]
        self.root.addLayout(bar)
        self.table = table(["ID", "Title", "Subject", "Updated", "Preview"])
        self.root.addWidget(self.table)

    def refresh(self):
        names = {s.id: s.name for s in self.service.repos.subjects.all()}
        term = self.search.text().casefold()
        items = [
            n
            for n in self.service.repos.notes.all()
            if term in (n.title + " " + n.content).casefold()
        ]
        fill_table(
            self.table,
            [
                (
                    n.id,
                    n.title,
                    names.get(n.subject_id, "Missing subject"),
                    n.updated_at[:16].replace("T", " "),
                    n.content.replace("\n", " ")[:80],
                )
                for n in items
            ],
        )

    def add(self):
        d = NoteDialog(self.service.repos.subjects.all(), parent=self)
        if d.exec():
            self.guard(lambda: self.service.create_note(*d.values()))
            self.changed.emit()

    def edit(self):
        item = self.service.repos.notes.get(selected_id(self.table))
        if not item:
            return
        d = NoteDialog(self.service.repos.subjects.all(), item, self)
        if d.exec():
            self.guard(lambda: self.service.update_note(item.id, *d.values()))
            self.changed.emit()

    def delete(self):
        item = self.service.repos.notes.get(selected_id(self.table))
        if (
            item
            and QMessageBox.question(self, "Delete note", f'Delete "{item.title}"?')
            == QMessageBox.Yes
        ):
            self.service.repos.notes.delete(item.id)
            self.changed.emit()


class PlannerPage(Page):
    def __init__(self, service):
        super().__init__(
            service, "Planner", "Schedule sessions and track actual study time."
        )
        bar = QHBoxLayout()
        add = QPushButton("Plan Session")
        add.setObjectName("Primary")
        add.clicked.connect(self.add)
        complete = QPushButton("Complete")
        complete.clicked.connect(self.complete)
        start = QPushButton("Start Timer")
        start.clicked.connect(self.start_timer)
        [bar.addWidget(x) for x in (add, complete, start)]
        bar.addStretch()
        self.timer_label = QLabel("Timer ready")
        bar.addWidget(self.timer_label)
        self.root.addLayout(bar)
        self.table = table(
            ["ID", "Date", "Start", "Subject", "Planned", "Actual", "Status"]
        )
        self.root.addWidget(self.table)
        self.elapsed = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)

    def refresh(self):
        names = {s.id: s.name for s in self.service.repos.subjects.all()}
        items = sorted(
            self.service.repos.sessions.all(),
            key=lambda s: (s.date, s.start_time),
            reverse=True,
        )
        fill_table(
            self.table,
            [
                (
                    s.id,
                    display_date(s.date),
                    s.start_time,
                    names.get(s.subject_id, "Missing subject"),
                    f"{s.planned_minutes} min",
                    f"{s.actual_minutes} min",
                    s.status,
                )
                for s in items
            ],
        )

    def add(self):
        d = SessionDialog(
            self.service.repos.subjects.all(), self.service.repos.tasks.all(), self
        )
        if d.exec():
            self.guard(lambda: self.service.create_session(*d.values()))
            self.changed.emit()

    def complete(self):
        item = self.service.repos.sessions.get(selected_id(self.table))
        if not item:
            return
        minutes, ok = QSpinBox(), False
        box = QMessageBox(self)
        box.setWindowTitle("Complete session")
        box.setText(
            f"Mark this session complete with {item.planned_minutes} actual minutes?"
        )
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if box.exec() == QMessageBox.Yes:
            self.guard(
                lambda: self.service.complete_session(item.id, item.planned_minutes)
            )
            self.changed.emit()

    def start_timer(self):
        item = self.service.repos.sessions.get(selected_id(self.table))
        if not item:
            QMessageBox.information(
                self, "Study timer", "Select a planned session first."
            )
            return
        self.active = item
        self.elapsed = 0
        self.timer.start(1000)
        self.timer_label.setText("00:00 — studying")

    def tick(self):
        self.elapsed += 1
        self.timer_label.setText(
            f"{self.elapsed//60:02}:{self.elapsed%60:02} — studying"
        )
        if self.elapsed >= self.active.planned_minutes * 60:
            self.timer.stop()
            self.service.complete_session(self.active.id, max(1, self.elapsed // 60))
            self.changed.emit()
            QMessageBox.information(
                self, "Session complete", "Great work! Your study session was saved."
            )


class FlashcardsPage(Page):
    def __init__(self, service):
        super().__init__(
            service, "Flashcards", "Review cards that need attention first."
        )
        bar = QHBoxLayout()
        add = QPushButton("Add Flashcard")
        add.setObjectName("Primary")
        add.clicked.connect(self.add)
        study = QPushButton("Study Selected")
        study.clicked.connect(self.study)
        delete = QPushButton("Delete")
        delete.setObjectName("Danger")
        delete.clicked.connect(self.delete)
        [bar.addWidget(x) for x in (add, study, delete)]
        bar.addStretch()
        self.root.addLayout(bar)
        self.table = table(
            [
                "ID",
                "Subject",
                "Question",
                "Difficulty",
                "Correct",
                "Wrong",
                "Last reviewed",
            ]
        )
        self.root.addWidget(self.table)

    def refresh(self):
        names = {s.id: s.name for s in self.service.repos.subjects.all()}
        items = sorted(
            self.service.repos.flashcards.all(),
            key=lambda c: -(c.wrong_count * 3 - c.correct_count),
        )
        fill_table(
            self.table,
            [
                (
                    c.id,
                    names.get(c.subject_id, "Missing subject"),
                    c.question,
                    c.difficulty,
                    c.correct_count,
                    c.wrong_count,
                    display_date(c.last_reviewed),
                )
                for c in items
            ],
        )

    def add(self):
        d = FlashcardDialog(self.service.repos.subjects.all(), parent=self)
        if d.exec():
            self.guard(lambda: self.service.create_flashcard(*d.values()))
            self.changed.emit()

    def study(self):
        card_item = self.service.repos.flashcards.get(selected_id(self.table))
        if not card_item:
            return
        QMessageBox.information(self, "Flashcard", card_item.question)
        answer = QMessageBox(self)
        answer.setWindowTitle("Answer")
        answer.setText(card_item.answer)
        buttons = {
            rating: answer.addButton(rating.title(), QMessageBox.ActionRole)
            for rating in ("AGAIN", "HARD", "GOOD", "EASY")
        }
        answer.exec()
        rating = next(
            (
                key
                for key, button in buttons.items()
                if answer.clickedButton() == button
            ),
            None,
        )
        if rating:
            self.service.review_flashcard(card_item.id, rating)
            self.changed.emit()

    def delete(self):
        item = self.service.repos.flashcards.get(selected_id(self.table))
        if (
            item
            and QMessageBox.question(self, "Delete flashcard", "Delete this flashcard?")
            == QMessageBox.Yes
        ):
            self.service.repos.flashcards.delete(item.id)
            self.changed.emit()


class QuizPage(Page):
    def __init__(self, service):
        super().__init__(
            service, "Quiz", "Create quizzes, answer them and review results."
        )
        bar = QHBoxLayout()
        add = QPushButton("Create Quiz")
        add.setObjectName("Primary")
        add.clicked.connect(self.add)
        take = QPushButton("Take Quiz")
        take.clicked.connect(self.take)
        delete = QPushButton("Delete")
        delete.setObjectName("Danger")
        delete.clicked.connect(self.delete)
        [bar.addWidget(x) for x in (add, take, delete)]
        bar.addStretch()
        self.root.addLayout(bar)
        self.table = table(["ID", "Title", "Subject", "Questions", "Best result"])
        self.root.addWidget(self.table)

    def refresh(self):
        names = {s.id: s.name for s in self.service.repos.subjects.all()}
        questions = self.service.repos.questions.all()
        results = self.service.repos.results.all()
        rows = []
        for q in self.service.repos.quizzes.all():
            count = sum(x.quiz_id == q.id for x in questions)
            scores = [x.accuracy for x in results if x.quiz_id == q.id]
            rows.append(
                (
                    q.id,
                    q.title,
                    names.get(q.subject_id, "Missing subject"),
                    count,
                    f"{max(scores):.0f}%" if scores else "Not taken",
                )
            )
        fill_table(self.table, rows)

    def add(self):
        d = QuizDialog(self.service.repos.subjects.all(), self)
        if d.exec():
            self.guard(lambda: self.service.create_quiz(*d.values()))
            self.changed.emit()

    def take(self):
        quiz = self.service.repos.quizzes.get(selected_id(self.table))
        if not quiz:
            return
        questions = [
            q for q in self.service.repos.questions.all() if q.quiz_id == quiz.id
        ]
        answers = {}
        review = []
        for q in questions:
            box = QMessageBox(self)
            box.setWindowTitle(quiz.title)
            box.setText(q.question_text)
            buttons = {
                letter: box.addButton(
                    f"{letter}. {getattr(q,'option_'+letter.lower())}",
                    QMessageBox.ActionRole,
                )
                for letter in "ABCD"
            }
            box.exec()
            chosen = next(
                (
                    letter
                    for letter, button in buttons.items()
                    if box.clickedButton() == button
                ),
                "",
            )
            answers[q.id] = chosen
            review.append(
                f'{"Correct" if chosen==q.correct_option else "Wrong"}: {q.question_text}\nAnswer: {q.correct_option}. {getattr(q,"option_"+q.correct_option.lower())}\n{q.explanation}'
            )
        result = self.service.submit_quiz(quiz.id, answers)
        QMessageBox.information(
            self,
            "Quiz result",
            f"Score: {result.score} / {result.total}\nAccuracy: {result.accuracy:.0f}%\n\n"
            + "\n\n".join(review),
        )
        self.changed.emit()

    def delete(self):
        quiz = self.service.repos.quizzes.get(selected_id(self.table))
        if (
            quiz
            and QMessageBox.question(
                self, "Delete quiz", f'Delete "{quiz.title}" and its results?'
            )
            == QMessageBox.Yes
        ):
            self.service.delete_quiz(quiz.id)
            self.changed.emit()


class StatisticsPage(Page):
    def __init__(self, service):
        super().__init__(
            service, "Statistics", "Locally calculated progress from your CSV data."
        )
        self.grid = QGridLayout()
        self.items = {}
        for i, (key, label) in enumerate(
            (
                ("study_minutes", "Study time this week"),
                ("average_quiz", "Average quiz"),
                ("flashcard_accuracy", "Flashcard accuracy"),
                ("streak", "Study streak"),
                ("most_studied", "Most studied"),
                ("completed_tasks", "Tasks completed"),
            )
        ):
            self.items[key] = card(label)
            self.grid.addWidget(self.items[key], i // 3, i % 3)
        self.root.addLayout(self.grid)
        self.charts = StudyCharts()
        self.root.addWidget(self.charts)

    def refresh(self):
        s = StatisticsService(self.service.repos).summary()
        self.items["study_minutes"].value_label.setText(f'{s["study_minutes"]} min')
        self.items["average_quiz"].value_label.setText(f'{s["average_quiz"]}%')
        self.items["flashcard_accuracy"].value_label.setText(
            f'{s["flashcard_accuracy"]}%'
        )
        self.items["streak"].value_label.setText(f'{s["streak"]} days')
        self.items["most_studied"].value_label.setText(str(s["most_studied"]))
        self.items["completed_tasks"].value_label.setText(
            f'{s["completed_tasks"]} / {s["weekly_tasks"]}'
        )
        self.charts.update_data(s["by_subject"], s["by_day"])


class AssistantPage(Page):
    def __init__(self, service):
        super().__init__(
            service,
            "Smart Assistant",
            "Personalized recommendations based on your study data.",
        )
        self.message = QTextEdit()
        self.message.setReadOnly(True)
        self.root.addWidget(self.message)
        planbar = QHBoxLayout()
        planbar.addWidget(QLabel("Available time"))
        self.minutes = QSpinBox()
        self.minutes.setRange(10, 240)
        self.minutes.setValue(60)
        self.minutes.setSuffix(" minutes")
        button = QPushButton("Build Study Plan")
        button.setObjectName("Primary")
        button.clicked.connect(self.build_plan)
        planbar.addWidget(self.minutes)
        planbar.addWidget(button)
        planbar.addStretch()
        self.root.addLayout(planbar)
        self.plan = QTextEdit()
        self.plan.setReadOnly(True)
        self.root.addWidget(self.plan)

    def refresh(self):
        self.message.setPlainText(AssistantService(self.service.repos).message())

    def build_plan(self):
        plan = AssistantService(self.service.repos).study_plan(self.minutes.value())
        self.plan.setPlainText(
            "\n".join(
                f'{index}. {item["subject"]} — {item["minutes"]} minutes (priority {item["score"]})'
                for index, item in enumerate(plan, 1)
            )
            or "Add study data or increase available time to build a plan."
        )


class SettingsPage(Page):
    def __init__(self, service):
        super().__init__(
            service, "Settings", "Profile, local data files and application tools."
        )
        form = QFormLayout()
        self.name = QLineEdit()
        self.duration = QSpinBox()
        self.duration.setRange(5, 240)
        self.duration.setSuffix(" minutes")
        save = QPushButton("Save Settings")
        save.setObjectName("Primary")
        save.clicked.connect(self.save)
        form.addRow("Student name", self.name)
        form.addRow("Default study duration", self.duration)
        form.addRow("Theme", QLabel("Light"))
        form.addRow("", save)
        self.root.addLayout(form)
        self.files = QTextEdit()
        self.files.setReadOnly(True)
        self.files.setMaximumHeight(190)
        self.root.addWidget(QLabel("Data Files"))
        self.root.addWidget(self.files)
        bar = QHBoxLayout()
        for text, callback, name in (
            ("Open Data Folder", self.open_folder, ""),
            ("Load Demo Data", self.demo, ""),
            ("Reload Data", lambda: self.changed.emit(), ""),
            ("Export Tasks", lambda: self.export("Tasks"), ""),
            ("Export Study History", lambda: self.export("Study History"), ""),
            ("Reset Application Data", self.reset, "Danger"),
        ):
            button = QPushButton(text)
            button.setObjectName(name)
            button.clicked.connect(callback)
            bar.addWidget(button)
        self.root.addLayout(bar)
        self.root.addStretch()
        version = QLabel(
            "StudyFlow — Version 0.1.0\nOffline CSV study assistant. No generative AI or external API."
        )
        version.setObjectName("Muted")
        self.root.addWidget(version)

    def refresh(self):
        self.name.setText(self.service.repos.profile.get_name())
        self.duration.setValue(
            int(self.service.repos.settings.get("default_study_duration", "30"))
        )
        lines = []
        for label, repo in (
            ("subjects.csv", self.service.repos.subjects),
            ("tasks.csv", self.service.repos.tasks),
            ("study_sessions.csv", self.service.repos.sessions),
            ("notes.csv", self.service.repos.notes),
            ("flashcards.csv", self.service.repos.flashcards),
            ("quizzes.csv", self.service.repos.quizzes),
            ("quiz_results.csv", self.service.repos.results),
        ):
            lines.append(f"{label:<24} {len(repo.storage.read_all())} records")
        self.files.setPlainText("\n".join(lines))

    def save(self):
        self.guard(
            lambda: self.service.setup_profile(self.name.text(), self.duration.value())
        )
        self.changed.emit()

    def demo(self):
        if (
            QMessageBox.question(
                self,
                "Load demo data",
                "Replace current records with complete demo data?",
            )
            == QMessageBox.Yes
        ):
            self.service.load_demo()
            self.changed.emit()

    def reset(self):
        if (
            QMessageBox.question(
                self,
                "Reset application data",
                "This will permanently delete your local data.\n\nContinue?",
            )
            == QMessageBox.Yes
        ):
            self.service.reset()
            self.changed.emit()

    def open_folder(self):
        os.startfile(str(self.service.repos.data_dir))

    def export(self, name):
        path = self.guard(lambda: self.service.export(name))
        if path:
            QMessageBox.information(self, "Export complete", f"Saved to:\n{path}")
