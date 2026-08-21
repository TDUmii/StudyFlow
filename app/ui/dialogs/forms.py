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

from app.i18n import SUPPORTED_LANGUAGES, language_manager, tr
from app.data.subject_catalog import (
    CATALOG_BY_KEY,
    catalog_options,
    infer_catalog_key,
    subject_display_name,
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
        self.buttons.button(QDialogButtonBox.Save).setText(tr("common.save"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(tr("common.cancel"))
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def validate_and_accept(self):
        try:
            self.validate()
        except ValidationError as exc:
            QMessageBox.warning(self, tr("dialog.check_information"), str(exc))
            return
        self.accept()

    def validate(self):
        pass


def subject_combo(subjects, selected=None):
    combo = QComboBox()
    for subject in subjects:
        combo.addItem(subject_display_name(subject), subject.id)
    if selected is not None:
        index = combo.findData(int(selected))
        combo.setCurrentIndex(max(0, index))
    return combo


class OnboardingDialog(FormDialog):
    def __init__(self, parent=None):
        super().__init__(tr("onboarding.title"), parent)
        self.name = QLineEdit()
        self.name.setPlaceholderText(tr("onboarding.name_placeholder"))
        self.duration = QSpinBox()
        self.duration.setRange(5, 240)
        self.duration.setValue(30)
        self.duration.setSuffix(f" {tr('common.minutes')}")
        self.language = QComboBox()
        for code, language in SUPPORTED_LANGUAGES.items():
            self.language.addItem(language["native_name"], code)
        self.form.addRow(tr("onboarding.your_name"), self.name)
        self.form.addRow(tr("onboarding.default_session"), self.duration)
        self.form.addRow("Language / Ngôn ngữ", self.language)
        self.language.currentIndexChanged.connect(self.change_language)

    def change_language(self):
        language_manager.set_language(self.language.currentData(), emit=False)
        self.setWindowTitle(tr("onboarding.title"))
        self.name.setPlaceholderText(tr("onboarding.name_placeholder"))
        self.duration.setSuffix(f" {tr('common.minutes')}")
        self.form.labelForField(self.name).setText(tr("onboarding.your_name"))
        self.form.labelForField(self.duration).setText(tr("onboarding.default_session"))
        self.buttons.button(QDialogButtonBox.Save).setText(tr("common.save"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(tr("common.cancel"))

    def validate(self):
        if not self.name.text().strip():
            raise ValidationError(tr("onboarding.name_required"))

    def values(self):
        return (
            self.name.text().strip(),
            self.duration.value(),
            self.language.currentData(),
        )


class SubjectDialog(FormDialog):
    def __init__(self, subject=None, parent=None):
        super().__init__(
            tr("dialog.edit_subject") if subject else tr("dialog.add_subject"), parent
        )
        current_key = (
            (subject.catalog_key or infer_catalog_key(subject.name)) if subject else ""
        )
        self.catalog = QComboBox()
        self.catalog.addItem(tr("subjects.custom_subject"), "")
        for key, label, _color in catalog_options():
            self.catalog.addItem(label, key)
        self.catalog.setCurrentIndex(max(0, self.catalog.findData(current_key)))
        self.name = QLineEdit(subject.name if subject and not current_key else "")
        self.name_vi = QLineEdit(subject.name_vi if subject and not current_key else "")
        self.color = QLineEdit(subject.color if subject else "#6366F1")
        self.description = QTextEdit(subject.description if subject else "")
        self.description.setMaximumHeight(90)
        self.target = QSpinBox()
        self.target.setRange(1, 100)
        self.target.setValue(subject.target_score if subject else 80)
        self.target.setSuffix("%")
        self.form.addRow(tr("subjects.library"), self.catalog)
        self.form.addRow(tr("subjects.name_en"), self.name)
        self.form.addRow(tr("subjects.name_vi"), self.name_vi)
        self.form.addRow(tr("field.color_hex"), self.color)
        self.form.addRow(tr("field.description"), self.description)
        self.form.addRow(tr("field.target_score"), self.target)
        self.catalog.currentIndexChanged.connect(self._catalog_changed)
        self._catalog_changed()

    def _catalog_changed(self):
        is_custom = not bool(self.catalog.currentData())
        self.name.setEnabled(is_custom)
        self.name_vi.setEnabled(is_custom)
        if not is_custom:
            definition = CATALOG_BY_KEY[self.catalog.currentData()]
            self.color.setText(definition.color)

    def validate(self):
        if not self.catalog.currentData() and (
            not self.name.text().strip() or not self.name_vi.text().strip()
        ):
            raise ValidationError(tr("subjects.custom_names_required"))

    def values(self):
        return {
            "name": self.name.text(),
            "name_vi": self.name_vi.text(),
            "catalog_key": self.catalog.currentData(),
            "color": self.color.text(),
            "description": self.description.toPlainText(),
            "target_score": self.target.value(),
        }


class TaskDialog(FormDialog):
    def __init__(self, subjects, task=None, parent=None):
        super().__init__(
            tr("dialog.edit_task") if task else tr("dialog.add_task"), parent
        )
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
        for code in ("LOW", "MEDIUM", "HIGH"):
            self.priority.addItem(tr(f"priority.{code.lower()}"), code)
        self.priority.setCurrentIndex(
            self.priority.findData(task.priority if task else "MEDIUM")
        )
        self.minutes = QSpinBox()
        self.minutes.setRange(1, 600)
        self.minutes.setValue(task.estimated_minutes if task else 30)
        self.minutes.setSuffix(f" {tr('common.minutes')}")
        self.description = QTextEdit(task.description if task else "")
        self.description.setMaximumHeight(80)
        for label, widget in (
            (tr("field.title"), self.title),
            (tr("field.subject"), self.subject),
            (tr("field.deadline"), self.deadline),
            (tr("field.priority"), self.priority),
            (tr("field.estimated_time"), self.minutes),
            (tr("field.description"), self.description),
        ):
            self.form.addRow(label, widget)

    def validate(self):
        if not self.title.text().strip():
            raise ValidationError(tr("validation.required", label=tr("field.title")))
        if self.subject.currentData() is None:
            raise ValidationError(tr("validation.create_subject_first"))

    def values(self):
        return {
            "title": self.title.text(),
            "subject_id": self.subject.currentData(),
            "deadline": self.deadline.date().toString("yyyy-MM-dd"),
            "priority": self.priority.currentData(),
            "minutes": self.minutes.value(),
            "description": self.description.toPlainText(),
        }


class NoteDialog(FormDialog):
    def __init__(self, subjects, note=None, parent=None):
        super().__init__(
            tr("dialog.edit_note") if note else tr("dialog.add_note"), parent
        )
        self.resize(520, 400)
        self.title = QLineEdit(note.title if note else "")
        self.subject = subject_combo(subjects, note.subject_id if note else None)
        self.content = QTextEdit(note.content if note else "")
        self.form.addRow(tr("field.title"), self.title)
        self.form.addRow(tr("field.subject"), self.subject)
        self.form.addRow(tr("field.content"), self.content)

    def validate(self):
        if not self.title.text().strip() or not self.content.toPlainText().strip():
            raise ValidationError(tr("validation.title_content"))
        if self.subject.currentData() is None:
            raise ValidationError(tr("validation.create_subject_first"))

    def values(self):
        return self.title.text(), self.subject.currentData(), self.content.toPlainText()


class FlashcardDialog(FormDialog):
    def __init__(self, subjects, card=None, parent=None):
        super().__init__(
            tr("dialog.edit_flashcard") if card else tr("dialog.add_flashcard"),
            parent,
        )
        self.subject = subject_combo(subjects, card.subject_id if card else None)
        self.question = QTextEdit(card.question if card else "")
        self.answer = QTextEdit(card.answer if card else "")
        self.question.setMaximumHeight(100)
        self.answer.setMaximumHeight(100)
        self.form.addRow(tr("field.subject"), self.subject)
        self.form.addRow(tr("field.question"), self.question)
        self.form.addRow(tr("field.answer"), self.answer)

    def validate(self):
        if (
            self.subject.currentData() is None
            or not self.question.toPlainText().strip()
            or not self.answer.toPlainText().strip()
        ):
            raise ValidationError(tr("validation.flashcard_fields"))

    def values(self):
        return (
            self.subject.currentData(),
            self.question.toPlainText(),
            self.answer.toPlainText(),
        )


class SessionDialog(FormDialog):
    def __init__(self, subjects, tasks, parent=None):
        super().__init__(tr("dialog.plan_session"), parent)
        self.subject = subject_combo(subjects)
        self.task = QComboBox()
        self.task.addItem(tr("planner.no_linked_task"), "")
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
        self.minutes.setSuffix(f" {tr('common.minutes')}")
        self.note = QLineEdit()
        for label, w in (
            (tr("field.subject"), self.subject),
            (tr("field.task"), self.task),
            (tr("field.date"), self.date),
            (tr("field.start_time"), self.time),
            (tr("field.planned_time"), self.minutes),
            (tr("field.note"), self.note),
        ):
            self.form.addRow(label, w)

    def validate(self):
        if self.subject.currentData() is None:
            raise ValidationError(tr("validation.create_subject_first"))

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
        super().__init__(tr("dialog.create_quiz"), parent)
        self.resize(520, 560)
        self.subject = subject_combo(subjects)
        self.title = QLineEdit()
        self.description = QLineEdit()
        self.question = QLineEdit()
        self.options = [QLineEdit() for _ in range(4)]
        self.correct = QComboBox()
        self.correct.addItems(list("ABCD"))
        self.explanation = QLineEdit()
        self.form.addRow(tr("field.subject"), self.subject)
        self.form.addRow(tr("field.quiz_title"), self.title)
        self.form.addRow(tr("field.description"), self.description)
        self.form.addRow(tr("field.question"), self.question)
        for letter, widget in zip("ABCD", self.options):
            self.form.addRow(tr("field.option", letter=letter), widget)
        self.form.addRow(tr("field.correct_option"), self.correct)
        self.form.addRow(tr("field.explanation"), self.explanation)

    def validate(self):
        if self.subject.currentData() is None:
            raise ValidationError(tr("validation.create_subject_first"))
        if (
            not self.title.text().strip()
            or not self.question.text().strip()
            or any(not x.text().strip() for x in self.options)
        ):
            raise ValidationError(tr("validation.quiz_fields"))

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
