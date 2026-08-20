from __future__ import annotations

import logging
from pathlib import Path
from typing import Generic, TypeVar

from app.models import (
    Flashcard,
    Note,
    Quiz,
    QuizQuestion,
    QuizResult,
    StudySession,
    Subject,
    Task,
)
from app.storage import CSVStorage, SCHEMAS
from app.utils.helpers import next_id

LOGGER = logging.getLogger(__name__)
T = TypeVar("T")


class ModelRepository(Generic[T]):
    def __init__(self, data_dir: Path, name: str, model_class: type[T]):
        self.name = name
        self.model_class = model_class
        self.storage = CSVStorage(data_dir / f"{name}.csv", SCHEMAS[name])

    def all(self) -> list[T]:
        records: list[T] = []
        for row in self.storage.read_all():
            try:
                record = self.model_class.from_dict(row)
                if hasattr(record, "id") and int(getattr(record, "id")) <= 0:
                    raise ValueError("invalid id")
                records.append(record)
            except (TypeError, ValueError) as exc:
                LOGGER.warning("Skipped invalid %s row: %s", self.name, exc)
        return records

    def get(self, record_id: int | str) -> T | None:
        return next(
            (
                record
                for record in self.all()
                if str(getattr(record, "id", "")) == str(record_id)
            ),
            None,
        )

    def add(self, record: T) -> T:
        self.storage.append(record.to_dict())
        return record

    def create_id(self) -> int:
        return next_id(self.storage.read_all())

    def update(self, record: T) -> bool:
        return self.storage.update(getattr(record, "id"), record.to_dict())

    def delete(self, record_id: int | str) -> bool:
        return self.storage.delete(record_id)

    def clear(self) -> None:
        self.storage.write_all([])


class KeyValueRepository:
    def __init__(self, data_dir: Path):
        self.storage = CSVStorage(data_dir / "settings.csv", SCHEMAS["settings"])

    def all(self) -> dict[str, str]:
        return {
            row["key"]: row["value"]
            for row in self.storage.read_all()
            if row.get("key")
        }

    def get(self, key: str, default: str = "") -> str:
        return self.all().get(key, default)

    def set(self, key: str, value: object) -> None:
        rows = self.storage.read_all()
        for row in rows:
            if row["key"] == key:
                row["value"] = str(value)
                self.storage.write_all(rows)
                return
        self.storage.append({"key": key, "value": str(value)})


class ProfileRepository:
    def __init__(self, data_dir: Path):
        self.storage = CSVStorage(data_dir / "profile.csv", SCHEMAS["profile"])

    def get_name(self) -> str:
        rows = self.storage.read_all()
        return rows[0].get("name", "") if rows else ""

    def save(self, name: str, created_at: str) -> None:
        self.storage.write_all([{"name": name, "created_at": created_at}])


class RepositoryBundle:
    def __init__(self, data_dir: Path | str):
        data_dir = Path(data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = data_dir
        self.profile = ProfileRepository(data_dir)
        self.settings = KeyValueRepository(data_dir)
        self.subjects = ModelRepository(data_dir, "subjects", Subject)
        self.tasks = ModelRepository(data_dir, "tasks", Task)
        self.sessions = ModelRepository(data_dir, "study_sessions", StudySession)
        self.notes = ModelRepository(data_dir, "notes", Note)
        self.flashcards = ModelRepository(data_dir, "flashcards", Flashcard)
        self.quizzes = ModelRepository(data_dir, "quizzes", Quiz)
        self.questions = ModelRepository(data_dir, "quiz_questions", QuizQuestion)
        self.results = ModelRepository(data_dir, "quiz_results", QuizResult)

    def ensure_all(self) -> None:
        for name, fields in SCHEMAS.items():
            CSVStorage(self.data_dir / f"{name}.csv", fields)
