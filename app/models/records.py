"""Domain models illustrate object ↔ dictionary ↔ CSV conversion."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields


class RecordMixin:
    def to_dict(self) -> dict[str, str]:
        return {
            key: "" if value is None else str(value)
            for key, value in asdict(self).items()
        }

    @classmethod
    def from_dict(cls, row: dict[str, str]):
        values = {
            field.name: row.get(
                field.name, field.default if field.default is not None else ""
            )
            for field in fields(cls)
        }
        for field in fields(cls):
            if field.type is int or field.type == "int":
                try:
                    values[field.name] = int(values[field.name])
                except (TypeError, ValueError):
                    values[field.name] = 0
            elif field.type is float or field.type == "float":
                try:
                    values[field.name] = float(values[field.name])
                except (TypeError, ValueError):
                    values[field.name] = 0.0
        return cls(**values)


@dataclass
class Subject(RecordMixin):
    id: int
    name: str
    color: str = "#6366F1"
    description: str = ""
    target_score: int = 80
    created_at: str = ""
    catalog_key: str = ""
    name_vi: str = ""


@dataclass
class Task(RecordMixin):
    id: int
    title: str
    description: str
    subject_id: int
    deadline: str
    priority: str
    estimated_minutes: int
    status: str
    created_at: str
    completed_at: str = ""


@dataclass
class StudySession(RecordMixin):
    id: int
    subject_id: int
    task_id: str
    date: str
    start_time: str
    planned_minutes: int
    actual_minutes: int
    note: str
    status: str
    created_at: str


@dataclass
class Note(RecordMixin):
    id: int
    title: str
    subject_id: int
    content: str
    created_at: str
    updated_at: str


@dataclass
class Flashcard(RecordMixin):
    id: int
    subject_id: int
    question: str
    answer: str
    difficulty: str
    correct_count: int
    wrong_count: int
    last_reviewed: str
    created_at: str


@dataclass
class Quiz(RecordMixin):
    id: int
    subject_id: int
    title: str
    description: str
    created_at: str


@dataclass
class QuizQuestion(RecordMixin):
    id: int
    quiz_id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str
    explanation: str


@dataclass
class QuizResult(RecordMixin):
    id: int
    quiz_id: int
    score: int
    total: int
    accuracy: float
    duration_seconds: int
    completed_at: str
