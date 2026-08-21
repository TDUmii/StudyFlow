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
from app.data.subject_catalog import subject_display_name, subject_search_text
from app.i18n import SUPPORTED_LANGUAGES, language_manager, tr
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


def status_text(code: str) -> str:
    return tr(f"status.{code.lower()}")


def priority_text(code: str) -> str:
    return tr(f"priority.{code.lower()}")


def rating_text(code: str) -> str:
    return tr(f"rating.{code.lower()}")


def confirm(parent: QWidget, title: str, message: str) -> bool:
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(message)
    yes_button = box.addButton(tr("common.yes"), QMessageBox.AcceptRole)
    box.addButton(tr("common.cancel"), QMessageBox.RejectRole)
    box.exec()
    return box.clickedButton() == yes_button


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
            QMessageBox.warning(self, tr("common.studyflow_message"), str(exc))


class DashboardPage(Page):
    def __init__(self, service):
        super().__init__(service, tr("nav.dashboard"), tr("dashboard.subtitle"))
        grid = QGridLayout()
        self.cards = {}
        for index, (key, label) in enumerate(
            (
                ("tasks_today", tr("dashboard.tasks_today")),
                ("study_minutes", tr("dashboard.study_week")),
                ("upcoming", tr("dashboard.upcoming")),
                ("streak", tr("dashboard.streak")),
            )
        ):
            self.cards[key] = card(label)
            grid.addWidget(self.cards[key], 0, index)
        self.root.addLayout(grid)
        title = QLabel(tr("dashboard.recommendation"))
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
        self.cards["study_minutes"].value_label.setText(
            f'{stats["study_minutes"]} {tr("common.minute_short")}'
        )
        self.cards["upcoming"].value_label.setText(str(stats["upcoming"]))
        self.cards["streak"].value_label.setText(
            f'{stats["streak"]} {tr("common.days")}'
        )
        self.recommendation.setText(AssistantService(self.service.repos).message())


class SubjectsPage(Page):
    def __init__(self, service):
        super().__init__(service, tr("nav.subjects"), tr("subjects.subtitle"))
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("subjects.search"))
        self.search.textChanged.connect(self.refresh)
        add = QPushButton(tr("dialog.add_subject"))
        add.setObjectName("Primary")
        add.clicked.connect(self.add)
        edit = QPushButton(tr("common.edit"))
        edit.clicked.connect(self.edit)
        delete = QPushButton(tr("common.delete"))
        delete.setObjectName("Danger")
        delete.clicked.connect(self.delete)
        [bar.addWidget(x) for x in (self.search, add, edit, delete)]
        self.root.addLayout(bar)
        self.table = table(
            [
                tr("table.id"),
                tr("table.name"),
                tr("table.target"),
                tr("table.description"),
            ]
        )
        self.root.addWidget(self.table)

    def refresh(self):
        term = self.search.text().casefold()
        items = [
            s
            for s in self.service.repos.subjects.all()
            if term in subject_search_text(s).casefold()
        ]
        fill_table(
            self.table,
            [
                (
                    s.id,
                    subject_display_name(s),
                    f"{s.target_score}%",
                    s.description,
                )
                for s in items
            ],
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
        if item and confirm(
            self,
            tr("subjects.delete_title"),
            tr("subjects.delete_message", name=subject_display_name(item)),
        ):
            self.guard(lambda: self.service.delete_subject(item.id))
            self.changed.emit()


class TasksPage(Page):
    def __init__(self, service):
        super().__init__(service, tr("nav.tasks"), tr("tasks.subtitle"))
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("tasks.search"))
        self.filter = QComboBox()
        for code in ("ALL", "TODO", "IN_PROGRESS", "COMPLETED"):
            self.filter.addItem(status_text(code), code)
        self.search.textChanged.connect(self.refresh)
        self.filter.currentTextChanged.connect(self.refresh)
        buttons = []
        for text, callback, name in (
            (tr("dialog.add_task"), self.add, "Primary"),
            (tr("common.edit"), self.edit, ""),
            (tr("common.start"), lambda: self.status("IN_PROGRESS"), ""),
            (tr("common.complete"), lambda: self.status("COMPLETED"), ""),
            (tr("common.delete"), self.delete, "Danger"),
        ):
            b = QPushButton(text)
            b.setObjectName(name)
            b.clicked.connect(callback)
            buttons.append(b)
        [bar.addWidget(x) for x in (self.search, self.filter, *buttons)]
        self.root.addLayout(bar)
        self.table = table(
            [
                tr("table.id"),
                tr("table.title"),
                tr("table.subject"),
                tr("table.deadline"),
                tr("table.priority"),
                tr("table.status"),
            ]
        )
        self.root.addWidget(self.table)

    def refresh(self):
        names = {
            s.id: subject_display_name(s) for s in self.service.repos.subjects.all()
        }
        term = self.search.text().casefold()
        status = self.filter.currentData()
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
                    names.get(t.subject_id, tr("common.missing_subject")),
                    display_date(t.deadline),
                    priority_text(t.priority),
                    status_text(t.status),
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
        if item and confirm(
            self,
            tr("tasks.delete_title"),
            tr("tasks.delete_message", name=item.title),
        ):
            self.service.repos.tasks.delete(item.id)
            self.changed.emit()


class NotesPage(Page):
    def __init__(self, service):
        super().__init__(
            service,
            tr("nav.notes"),
            tr("notes.subtitle"),
        )
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("notes.search"))
        self.search.textChanged.connect(self.refresh)
        add = QPushButton(tr("dialog.add_note"))
        add.setObjectName("Primary")
        add.clicked.connect(self.add)
        edit = QPushButton(tr("common.edit"))
        edit.clicked.connect(self.edit)
        delete = QPushButton(tr("common.delete"))
        delete.setObjectName("Danger")
        delete.clicked.connect(self.delete)
        [bar.addWidget(x) for x in (self.search, add, edit, delete)]
        self.root.addLayout(bar)
        self.table = table(
            [
                tr("table.id"),
                tr("table.title"),
                tr("table.subject"),
                tr("table.updated"),
                tr("table.preview"),
            ]
        )
        self.root.addWidget(self.table)

    def refresh(self):
        names = {
            s.id: subject_display_name(s) for s in self.service.repos.subjects.all()
        }
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
                    names.get(n.subject_id, tr("common.missing_subject")),
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
        if item and confirm(
            self,
            tr("notes.delete_title"),
            tr("notes.delete_message", name=item.title),
        ):
            self.service.repos.notes.delete(item.id)
            self.changed.emit()


class PlannerPage(Page):
    def __init__(self, service):
        super().__init__(service, tr("nav.planner"), tr("planner.subtitle"))
        bar = QHBoxLayout()
        add = QPushButton(tr("planner.plan_session"))
        add.setObjectName("Primary")
        add.clicked.connect(self.add)
        complete = QPushButton(tr("common.complete"))
        complete.clicked.connect(self.complete)
        start = QPushButton(tr("planner.start_timer"))
        start.clicked.connect(self.start_timer)
        [bar.addWidget(x) for x in (add, complete, start)]
        bar.addStretch()
        self.timer_label = QLabel(tr("planner.timer_ready"))
        bar.addWidget(self.timer_label)
        self.root.addLayout(bar)
        self.table = table(
            [
                tr("table.id"),
                tr("table.date"),
                tr("table.start"),
                tr("table.subject"),
                tr("table.planned"),
                tr("table.actual"),
                tr("table.status"),
            ]
        )
        self.root.addWidget(self.table)
        self.elapsed = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)

    def refresh(self):
        names = {
            s.id: subject_display_name(s) for s in self.service.repos.subjects.all()
        }
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
                    names.get(s.subject_id, tr("common.missing_subject")),
                    f"{s.planned_minutes} {tr('common.minute_short')}",
                    f"{s.actual_minutes} {tr('common.minute_short')}",
                    status_text(s.status),
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
        if confirm(
            self,
            tr("planner.complete_title"),
            tr("planner.complete_message", minutes=item.planned_minutes),
        ):
            self.guard(
                lambda: self.service.complete_session(item.id, item.planned_minutes)
            )
            self.changed.emit()

    def start_timer(self):
        item = self.service.repos.sessions.get(selected_id(self.table))
        if not item:
            QMessageBox.information(
                self, tr("planner.timer_title"), tr("planner.select_session")
            )
            return
        self.active = item
        self.elapsed = 0
        self.timer.start(1000)
        self.timer_label.setText(f"00:00 — {tr('planner.studying')}")

    def tick(self):
        self.elapsed += 1
        self.timer_label.setText(
            f"{self.elapsed//60:02}:{self.elapsed%60:02} — {tr('planner.studying')}"
        )
        if self.elapsed >= self.active.planned_minutes * 60:
            self.timer.stop()
            self.service.complete_session(self.active.id, max(1, self.elapsed // 60))
            self.changed.emit()
            QMessageBox.information(
                self, tr("planner.session_complete"), tr("planner.saved")
            )


class FlashcardsPage(Page):
    def __init__(self, service):
        super().__init__(service, tr("nav.flashcards"), tr("flashcards.subtitle"))
        bar = QHBoxLayout()
        add = QPushButton(tr("dialog.add_flashcard"))
        add.setObjectName("Primary")
        add.clicked.connect(self.add)
        study = QPushButton(tr("flashcards.study_selected"))
        study.clicked.connect(self.study)
        delete = QPushButton(tr("common.delete"))
        delete.setObjectName("Danger")
        delete.clicked.connect(self.delete)
        [bar.addWidget(x) for x in (add, study, delete)]
        bar.addStretch()
        self.root.addLayout(bar)
        self.table = table(
            [
                tr("table.id"),
                tr("table.subject"),
                tr("field.question"),
                tr("flashcards.difficulty"),
                tr("flashcards.correct"),
                tr("flashcards.wrong"),
                tr("flashcards.last_reviewed"),
            ]
        )
        self.root.addWidget(self.table)

    def refresh(self):
        names = {
            s.id: subject_display_name(s) for s in self.service.repos.subjects.all()
        }
        items = sorted(
            self.service.repos.flashcards.all(),
            key=lambda c: -(c.wrong_count * 3 - c.correct_count),
        )
        fill_table(
            self.table,
            [
                (
                    c.id,
                    names.get(c.subject_id, tr("common.missing_subject")),
                    c.question,
                    rating_text(c.difficulty),
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
        QMessageBox.information(
            self, tr("entity.flashcard").title(), card_item.question
        )
        answer = QMessageBox(self)
        answer.setWindowTitle(tr("field.answer"))
        answer.setText(card_item.answer)
        buttons = {
            rating: answer.addButton(rating_text(rating), QMessageBox.ActionRole)
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
        if item and confirm(
            self,
            tr("flashcards.delete_title"),
            tr("flashcards.delete_message"),
        ):
            self.service.repos.flashcards.delete(item.id)
            self.changed.emit()


class QuizPage(Page):
    def __init__(self, service):
        super().__init__(service, tr("nav.quiz"), tr("quiz.subtitle"))
        bar = QHBoxLayout()
        add = QPushButton(tr("dialog.create_quiz"))
        add.setObjectName("Primary")
        add.clicked.connect(self.add)
        take = QPushButton(tr("quiz.take"))
        take.clicked.connect(self.take)
        delete = QPushButton(tr("common.delete"))
        delete.setObjectName("Danger")
        delete.clicked.connect(self.delete)
        [bar.addWidget(x) for x in (add, take, delete)]
        bar.addStretch()
        self.root.addLayout(bar)
        self.table = table(
            [
                tr("table.id"),
                tr("table.title"),
                tr("table.subject"),
                tr("quiz.questions"),
                tr("quiz.best_result"),
            ]
        )
        self.root.addWidget(self.table)

    def refresh(self):
        names = {
            s.id: subject_display_name(s) for s in self.service.repos.subjects.all()
        }
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
                    names.get(q.subject_id, tr("common.missing_subject")),
                    count,
                    f"{max(scores):.0f}%" if scores else tr("quiz.not_taken"),
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
            result_label = (
                tr("quiz.correct") if chosen == q.correct_option else tr("quiz.wrong")
            )
            review.append(
                f'{result_label}: {q.question_text}\n{tr("quiz.answer")}: '
                f'{q.correct_option}. {getattr(q,"option_"+q.correct_option.lower())}\n'
                f"{q.explanation}"
            )
        result = self.service.submit_quiz(quiz.id, answers)
        QMessageBox.information(
            self,
            tr("quiz.result"),
            tr(
                "quiz.result_text",
                score=result.score,
                total=result.total,
                accuracy=f"{result.accuracy:.0f}",
                review="\n\n".join(review),
            ),
        )
        self.changed.emit()

    def delete(self):
        quiz = self.service.repos.quizzes.get(selected_id(self.table))
        if quiz and confirm(
            self,
            tr("quiz.delete_title"),
            tr("quiz.delete_message", name=quiz.title),
        ):
            self.service.delete_quiz(quiz.id)
            self.changed.emit()


class StatisticsPage(Page):
    def __init__(self, service):
        super().__init__(service, tr("nav.statistics"), tr("statistics.subtitle"))
        self.grid = QGridLayout()
        self.items = {}
        for i, (key, label) in enumerate(
            (
                ("study_minutes", tr("statistics.study_week")),
                ("average_quiz", tr("statistics.average_quiz")),
                ("flashcard_accuracy", tr("statistics.flashcard_accuracy")),
                ("streak", tr("statistics.streak")),
                ("most_studied", tr("statistics.most_studied")),
                ("completed_tasks", tr("statistics.tasks_completed")),
            )
        ):
            self.items[key] = card(label)
            self.grid.addWidget(self.items[key], i // 3, i % 3)
        self.root.addLayout(self.grid)
        self.charts = StudyCharts()
        self.root.addWidget(self.charts)

    def refresh(self):
        s = StatisticsService(self.service.repos).summary()
        self.items["study_minutes"].value_label.setText(
            f'{s["study_minutes"]} {tr("common.minute_short")}'
        )
        self.items["average_quiz"].value_label.setText(f'{s["average_quiz"]}%')
        self.items["flashcard_accuracy"].value_label.setText(
            f'{s["flashcard_accuracy"]}%'
        )
        self.items["streak"].value_label.setText(f'{s["streak"]} {tr("common.days")}')
        self.items["most_studied"].value_label.setText(str(s["most_studied"]))
        self.items["completed_tasks"].value_label.setText(
            f'{s["completed_tasks"]} / {s["weekly_tasks"]}'
        )
        self.charts.update_data(s["by_subject"], s["by_day"])


class AssistantPage(Page):
    def __init__(self, service):
        super().__init__(
            service,
            tr("nav.assistant"),
            tr("assistant.subtitle"),
        )
        self.message = QTextEdit()
        self.message.setReadOnly(True)
        self.root.addWidget(self.message)
        planbar = QHBoxLayout()
        planbar.addWidget(QLabel(tr("assistant.available_time")))
        self.minutes = QSpinBox()
        self.minutes.setRange(10, 240)
        self.minutes.setValue(60)
        self.minutes.setSuffix(f" {tr('common.minutes')}")
        button = QPushButton(tr("assistant.build_plan"))
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
                tr(
                    "assistant.plan_line",
                    index=index,
                    subject=item["subject"],
                    minutes=item["minutes"],
                    score=item["score"],
                )
                for index, item in enumerate(plan, 1)
            )
            or tr("assistant.plan_empty")
        )


class SettingsPage(Page):
    def __init__(self, service):
        super().__init__(service, tr("nav.settings"), tr("settings.subtitle"))
        form = QFormLayout()
        self.name = QLineEdit()
        self.duration = QSpinBox()
        self.duration.setRange(5, 240)
        self.duration.setSuffix(f" {tr('common.minutes')}")
        self.language = QComboBox()
        for code, language in SUPPORTED_LANGUAGES.items():
            self.language.addItem(language["native_name"], code)
        self.language.currentIndexChanged.connect(self.change_language)
        save = QPushButton(tr("settings.save"))
        save.setObjectName("Primary")
        save.clicked.connect(self.save)
        form.addRow(tr("label.student_name"), self.name)
        form.addRow(tr("settings.default_duration"), self.duration)
        form.addRow(tr("language.label"), self.language)
        form.addRow(tr("settings.theme"), QLabel(tr("settings.light")))
        form.addRow("", save)
        self.root.addLayout(form)
        self.files = QTextEdit()
        self.files.setReadOnly(True)
        self.files.setMaximumHeight(190)
        self.root.addWidget(QLabel(tr("settings.data_files")))
        self.root.addWidget(self.files)
        bar = QHBoxLayout()
        for text, callback, name in (
            (tr("settings.open_folder"), self.open_folder, ""),
            (tr("settings.load_demo"), self.demo, ""),
            (tr("settings.reload"), lambda: self.changed.emit(), ""),
            (tr("settings.export_tasks"), lambda: self.export("tasks"), ""),
            (
                tr("settings.export_history"),
                lambda: self.export("study_sessions"),
                "",
            ),
            (tr("settings.reset"), self.reset, "Danger"),
        ):
            button = QPushButton(text)
            button.setObjectName(name)
            button.clicked.connect(callback)
            bar.addWidget(button)
        self.root.addLayout(bar)
        self.root.addStretch()
        version = QLabel(tr("settings.about"))
        version.setObjectName("Muted")
        self.root.addWidget(version)

    def refresh(self):
        self.name.setText(self.service.repos.profile.get_name())
        self.duration.setValue(
            int(self.service.repos.settings.get("default_study_duration", "30"))
        )
        language_code = self.service.repos.settings.get(
            "language", language_manager.current_language
        )
        self.language.blockSignals(True)
        self.language.setCurrentIndex(max(0, self.language.findData(language_code)))
        self.language.blockSignals(False)
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
            lines.append(
                f"{label:<24} "
                f"{tr('settings.records', count=len(repo.storage.read_all()))}"
            )
        self.files.setPlainText("\n".join(lines))

    def save(self):
        self.guard(
            lambda: self.service.setup_profile(
                self.name.text(), self.duration.value(), self.language.currentData()
            )
        )
        self.changed.emit()

    def change_language(self):
        language_code = self.language.currentData()
        if not language_code:
            return
        self.service.repos.settings.set("language", language_code)
        language_manager.set_language(language_code)

    def demo(self):
        if confirm(
            self,
            tr("settings.demo_title"),
            tr("settings.demo_message"),
        ):
            self.service.load_demo()
            self.changed.emit()

    def reset(self):
        if confirm(
            self,
            tr("settings.reset_title"),
            tr("settings.reset_message"),
        ):
            self.service.reset()
            self.changed.emit()

    def open_folder(self):
        os.startfile(str(self.service.repos.data_dir))

    def export(self, name):
        path = self.guard(lambda: self.service.export(name))
        if path:
            QMessageBox.information(
                self,
                tr("settings.export_complete"),
                tr("settings.saved_to", path=path),
            )
