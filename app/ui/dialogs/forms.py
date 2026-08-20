from __future__ import annotations

from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
)

from app.utils.validators import ValidationError


class FormDialog(QDialog):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(430)
        self.layout = QVBoxLayout(self)
        self.form = QFormLayout()
        self.form.setSpacing(12)
        self.layout.addLayout(self.form)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def validate_and_accept(self):
        try:
            self.validate()
        except ValidationError as exc:
            QMessageBox.warning(self, "Check your information", str(exc))
            return
        self.accept()

    def validate(self):
        pass


def subject_combo(subjects, selected=None):
    combo = QComboBox()
    for subject in subjects:
        combo.addItem(subject.name, subject.id)
    if selected is not None:
        index = combo.findData(int(selected))
        combo.setCurrentIndex(max(0, index))
    return combo


class OnboardingDialog(FormDialog):
    def __init__(self, parent=None):
        super().__init__("Welcome to StudyFlow", parent)
        self.name = QLineEdit()
        self.name.setPlaceholderText("Your name")
        self.duration = QSpinBox()
        self.duration.setRange(5, 240)
        self.duration.setValue(30)
        self.duration.setSuffix(" minutes")
        self.form.addRow("Your name", self.name)
        self.form.addRow("Default study session", self.duration)

    def validate(self):
        if not self.name.text().strip():
            raise ValidationError("Your name is required.")

    def values(self):
        return self.name.text().strip(), self.duration.value()


class SubjectDialog(FormDialog):
    def __init__(self, subject=None, parent=None):
        super().__init__("Edit Subject" if subject else "Add Subject", parent)
        self.name = QLineEdit(subject.name if subject else "")
        self.color = QLineEdit(subject.color if subject else "#6366F1")
        self.description = QTextEdit(subject.description if subject else "")
        self.description.setMaximumHeight(90)
        self.target = QSpinBox()
        self.target.setRange(1, 100)
        self.target.setValue(subject.target_score if subject else 80)
        self.target.setSuffix("%")
        self.form.addRow("Name", self.name)
        self.form.addRow("Color (HEX)", self.color)
        self.form.addRow("Description", self.description)
        self.form.addRow("Target score", self.target)

    def validate(self):
        if not self.name.text().strip():
            raise ValidationError("Subject name is required.")

    def values(self):
        return {
            "name": self.name.text(),
            "color": self.color.text(),
            "description": self.description.toPlainText(),
            "target_score": self.target.value(),
        }


class TaskDialog(FormDialog):
    def __init__(self, subjects, task=None, parent=None):
        super().__init__("Edit Task" if task else "Add Task", parent)
        self.title = QLineEdit(task.title if task else "")
        self.subject = subject_combo(subjects, task.subject_id if task else None)
        self.deadline = QDateEdit()
        self.deadline.setCalendarPopup(True)
        self.deadline.setDisplayFormat("dd/MM/yyyy")
        self.deadline.setDate(
            QDate.fromString(task.deadline, "yyyy-MM-dd")
            if task
            else QDate.currentDate()
        )
        self.priority = QComboBox()
        self.priority.addItems(["LOW", "MEDIUM", "HIGH"])
        self.priority.setCurrentText(task.priority if task else "MEDIUM")
        self.minutes = QSpinBox()
        self.minutes.setRange(1, 600)
        self.minutes.setValue(task.estimated_minutes if task else 30)
        self.minutes.setSuffix(" minutes")
        self.description = QTextEdit(task.description if task else "")
        self.description.setMaximumHeight(80)
        for label, widget in (
            ("Title", self.title),
            ("Subject", self.subject),
            ("Deadline", self.deadline),
            ("Priority", self.priority),
            ("Estimated time", self.minutes),
            ("Description", self.description),
        ):
            self.form.addRow(label, widget)

    def validate(self):
        if not self.title.text().strip():
            raise ValidationError("Title is required.")
        if self.subject.currentData() is None:
            raise ValidationError("Create a subject first.")

    def values(self):
        return {
            "title": self.title.text(),
            "subject_id": self.subject.currentData(),
            "deadline": self.deadline.date().toString("yyyy-MM-dd"),
            "priority": self.priority.currentText(),
            "minutes": self.minutes.value(),
            "description": self.description.toPlainText(),
        }


class NoteDialog(FormDialog):
    def __init__(self, subjects, note=None, parent=None):
        super().__init__("Edit Note" if note else "Add Note", parent)
        self.resize(520, 400)
        self.title = QLineEdit(note.title if note else "")
        self.subject = subject_combo(subjects, note.subject_id if note else None)
        self.content = QTextEdit(note.content if note else "")
        self.form.addRow("Title", self.title)
        self.form.addRow("Subject", self.subject)
        self.form.addRow("Content", self.content)

    def validate(self):
        if not self.title.text().strip() or not self.content.toPlainText().strip():
            raise ValidationError("Title and content are required.")
        if self.subject.currentData() is None:
            raise ValidationError("Create a subject first.")

    def values(self):
        return self.title.text(), self.subject.currentData(), self.content.toPlainText()


class FlashcardDialog(FormDialog):
    def __init__(self, subjects, card=None, parent=None):
        super().__init__("Edit Flashcard" if card else "Add Flashcard", parent)
        self.subject = subject_combo(subjects, card.subject_id if card else None)
        self.question = QTextEdit(card.question if card else "")
        self.answer = QTextEdit(card.answer if card else "")
        self.question.setMaximumHeight(100)
        self.answer.setMaximumHeight(100)
        self.form.addRow("Subject", self.subject)
        self.form.addRow("Question", self.question)
        self.form.addRow("Answer", self.answer)

    def validate(self):
        if (
            self.subject.currentData() is None
            or not self.question.toPlainText().strip()
            or not self.answer.toPlainText().strip()
        ):
            raise ValidationError("Subject, question and answer are required.")

    def values(self):
        return (
            self.subject.currentData(),
            self.question.toPlainText(),
            self.answer.toPlainText(),
        )


class SessionDialog(FormDialog):
    def __init__(self, subjects, tasks, parent=None):
        super().__init__("Plan Study Session", parent)
        self.subject = subject_combo(subjects)
        self.task = QComboBox()
        self.task.addItem("No linked task", "")
        for task in tasks:
            self.task.addItem(task.title, str(task.id))
        self.date = QDateEdit(QDate.currentDate())
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat("dd/MM/yyyy")
        self.time = QTimeEdit(QTime.currentTime())
        self.time.setDisplayFormat("HH:mm")
        self.minutes = QSpinBox()
        self.minutes.setRange(1, 600)
        self.minutes.setValue(30)
        self.minutes.setSuffix(" minutes")
        self.note = QLineEdit()
        for label, w in (
            ("Subject", self.subject),
            ("Task", self.task),
            ("Date", self.date),
            ("Start time", self.time),
            ("Planned time", self.minutes),
            ("Note", self.note),
        ):
            self.form.addRow(label, w)

    def validate(self):
        if self.subject.currentData() is None:
            raise ValidationError("Create a subject first.")

    def values(self):
        return (
            self.subject.currentData(),
            self.date.date().toString("yyyy-MM-dd"),
            self.time.time().toString("HH:mm"),
            self.minutes.value(),
            self.task.currentData(),
            self.note.text(),
        )


class QuizDialog(FormDialog):
    """Creates a useful one-question quiz; more questions can be added as separate quizzes."""

    def __init__(self, subjects, parent=None):
        super().__init__("Create Quiz", parent)
        self.resize(520, 560)
        self.subject = subject_combo(subjects)
        self.title = QLineEdit()
        self.description = QLineEdit()
        self.question = QLineEdit()
        self.options = [QLineEdit() for _ in range(4)]
        self.correct = QComboBox()
        self.correct.addItems(list("ABCD"))
        self.explanation = QLineEdit()
        self.form.addRow("Subject", self.subject)
        self.form.addRow("Quiz title", self.title)
        self.form.addRow("Description", self.description)
        self.form.addRow("Question", self.question)
        for letter, widget in zip("ABCD", self.options):
            self.form.addRow(f"Option {letter}", widget)
        self.form.addRow("Correct option", self.correct)
        self.form.addRow("Explanation", self.explanation)

    def validate(self):
        if self.subject.currentData() is None:
            raise ValidationError("Create a subject first.")
        if (
            not self.title.text().strip()
            or not self.question.text().strip()
            or any(not x.text().strip() for x in self.options)
        ):
            raise ValidationError("Title, question and all four options are required.")

    def values(self):
        q = {
            "question_text": self.question.text(),
            **{
                f"option_{letter.lower()}": widget.text()
                for letter, widget in zip("ABCD", self.options)
            },
            "correct_option": self.correct.currentText(),
            "explanation": self.explanation.text(),
        }
        return (
            self.subject.currentData(),
            self.title.text(),
            self.description.text(),
            [q],
        )
