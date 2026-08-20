from __future__ import annotations

import csv
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path

from app.data.seed import load_demo_data
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
from app.repositories import RepositoryBundle
from app.storage import SCHEMAS
from app.utils.dates import now_iso
from app.utils.validators import ValidationError, integer_between, iso_date, required


class AppService:
    """Application facade: validation and cross-record business rules live here."""

    def __init__(self, data_dir: Path | str, export_dir: Path | str | None = None):
        self.repos = RepositoryBundle(data_dir)
        self.export_dir = Path(export_dir or Path(data_dir).parent / "exports")
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def setup_profile(self, name: str, duration: int = 30) -> None:
        self.repos.profile.save(required(name, "Student name"), now_iso())
        self.repos.settings.set(
            "default_study_duration", integer_between(duration, 5, 240, "Duration")
        )
        self.repos.settings.set("theme", "light")
        self.repos.settings.set("minimum_study_day", "10")

    def create_subject(
        self,
        name: str,
        color: str = "#6366F1",
        description: str = "",
        target_score: int = 80,
    ) -> Subject:
        name = required(name, "Subject name")
        if any(
            item.name.casefold() == name.casefold()
            for item in self.repos.subjects.all()
        ):
            raise ValidationError("A subject with this name already exists.")
        subject = Subject(
            self.repos.subjects.create_id(),
            name,
            color,
            description.strip(),
            integer_between(target_score, 1, 100, "Target score"),
            now_iso(),
        )
        return self.repos.subjects.add(subject)

    def update_subject(self, subject_id: int, **values) -> Subject:
        subject = self._require(self.repos.subjects.get(subject_id), "Subject")
        updated = replace(
            subject,
            name=required(values.get("name", subject.name), "Subject name"),
            color=values.get("color", subject.color),
            description=values.get("description", subject.description).strip(),
            target_score=integer_between(
                values.get("target_score", subject.target_score), 1, 100, "Target score"
            ),
        )
        self.repos.subjects.update(updated)
        return updated

    def delete_subject(self, subject_id: int) -> None:
        related = any(
            str(getattr(item, "subject_id", "")) == str(subject_id)
            for repo in (
                self.repos.tasks,
                self.repos.sessions,
                self.repos.notes,
                self.repos.flashcards,
                self.repos.quizzes,
            )
            for item in repo.all()
        )
        if related:
            raise ValidationError(
                "This subject is used by other records. Delete those records first."
            )
        self.repos.subjects.delete(subject_id)

    def create_task(
        self,
        title: str,
        subject_id: int,
        deadline: str,
        priority: str,
        minutes: int,
        description: str = "",
    ) -> Task:
        self._require_subject(subject_id)
        task = Task(
            self.repos.tasks.create_id(),
            required(title, "Title"),
            description.strip(),
            int(subject_id),
            iso_date(deadline, "Deadline"),
            self._choice(priority, {"LOW", "MEDIUM", "HIGH"}, "Priority"),
            integer_between(minutes, 1, 600, "Estimated time"),
            "TODO",
            now_iso(),
            "",
        )
        return self.repos.tasks.add(task)

    def update_task(self, task_id: int, **values) -> Task:
        task = self._require(self.repos.tasks.get(task_id), "Task")
        subject_id = int(values.get("subject_id", task.subject_id))
        self._require_subject(subject_id)
        updated = replace(
            task,
            title=required(values.get("title", task.title), "Title"),
            description=values.get("description", task.description).strip(),
            subject_id=subject_id,
            deadline=iso_date(values.get("deadline", task.deadline), "Deadline"),
            priority=self._choice(
                values.get("priority", task.priority),
                {"LOW", "MEDIUM", "HIGH"},
                "Priority",
            ),
            estimated_minutes=integer_between(
                values.get("minutes", task.estimated_minutes), 1, 600, "Estimated time"
            ),
        )
        self.repos.tasks.update(updated)
        return updated

    def set_task_status(self, task_id: int, status: str) -> None:
        task = self._require(self.repos.tasks.get(task_id), "Task")
        status = self._choice(status, {"TODO", "IN_PROGRESS", "COMPLETED"}, "Status")
        self.repos.tasks.update(
            replace(
                task,
                status=status,
                completed_at=now_iso() if status == "COMPLETED" else "",
            )
        )

    def create_note(self, title: str, subject_id: int, content: str) -> Note:
        self._require_subject(subject_id)
        note = Note(
            self.repos.notes.create_id(),
            required(title, "Title"),
            int(subject_id),
            required(content, "Content"),
            now_iso(),
            now_iso(),
        )
        return self.repos.notes.add(note)

    def update_note(
        self, note_id: int, title: str, subject_id: int, content: str
    ) -> Note:
        old = self._require(self.repos.notes.get(note_id), "Note")
        self._require_subject(subject_id)
        note = replace(
            old,
            title=required(title, "Title"),
            subject_id=int(subject_id),
            content=required(content, "Content"),
            updated_at=now_iso(),
        )
        self.repos.notes.update(note)
        return note

    def create_flashcard(
        self, subject_id: int, question: str, answer: str
    ) -> Flashcard:
        self._require_subject(subject_id)
        card = Flashcard(
            self.repos.flashcards.create_id(),
            int(subject_id),
            required(question, "Question"),
            required(answer, "Answer"),
            "NEW",
            0,
            0,
            "",
            now_iso(),
        )
        return self.repos.flashcards.add(card)

    def review_flashcard(self, card_id: int, rating: str) -> None:
        card = self._require(self.repos.flashcards.get(card_id), "Flashcard")
        rating = self._choice(rating, {"AGAIN", "HARD", "GOOD", "EASY"}, "Rating")
        correct = card.correct_count + (rating in {"GOOD", "EASY"})
        wrong = card.wrong_count + (rating in {"AGAIN", "HARD"})
        self.repos.flashcards.update(
            replace(
                card,
                difficulty=rating,
                correct_count=int(correct),
                wrong_count=int(wrong),
                last_reviewed=date.today().isoformat(),
            )
        )

    def create_session(
        self,
        subject_id: int,
        session_date: str,
        start_time: str,
        planned: int,
        task_id: str = "",
        note: str = "",
    ) -> StudySession:
        self._require_subject(subject_id)
        if task_id and not self.repos.tasks.get(task_id):
            raise ValidationError("The selected task no longer exists.")
        session = StudySession(
            self.repos.sessions.create_id(),
            int(subject_id),
            str(task_id),
            iso_date(session_date),
            start_time,
            integer_between(planned, 1, 600, "Planned time"),
            0,
            note.strip(),
            "PLANNED",
            now_iso(),
        )
        return self.repos.sessions.add(session)

    def complete_session(self, session_id: int, actual_minutes: int) -> None:
        session = self._require(self.repos.sessions.get(session_id), "Study session")
        self.repos.sessions.update(
            replace(
                session,
                actual_minutes=integer_between(actual_minutes, 1, 600, "Actual time"),
                status="COMPLETED",
            )
        )

    def create_quiz(
        self,
        subject_id: int,
        title: str,
        description: str,
        questions: list[dict[str, str]],
    ) -> Quiz:
        self._require_subject(subject_id)
        required(title, "Quiz title")
        if not questions:
            raise ValidationError("Add at least one question.")
        for question in questions:
            for key in (
                "question_text",
                "option_a",
                "option_b",
                "option_c",
                "option_d",
            ):
                required(question.get(key, ""), key.replace("_", " ").title())
            self._choice(
                question.get("correct_option", ""),
                {"A", "B", "C", "D"},
                "Correct option",
            )
        quiz = self.repos.quizzes.add(
            Quiz(
                self.repos.quizzes.create_id(),
                int(subject_id),
                title.strip(),
                description.strip(),
                now_iso(),
            )
        )
        for item in questions:
            self.repos.questions.add(
                QuizQuestion(
                    self.repos.questions.create_id(),
                    quiz.id,
                    item["question_text"].strip(),
                    item["option_a"].strip(),
                    item["option_b"].strip(),
                    item["option_c"].strip(),
                    item["option_d"].strip(),
                    item["correct_option"],
                    item.get("explanation", "").strip(),
                )
            )
        return quiz

    def submit_quiz(
        self, quiz_id: int, answers: dict[int, str], duration_seconds: int = 0
    ) -> QuizResult:
        self._require(self.repos.quizzes.get(quiz_id), "Quiz")
        questions = [
            item for item in self.repos.questions.all() if item.quiz_id == int(quiz_id)
        ]
        if not questions:
            raise ValidationError("This quiz has no valid questions.")
        score = sum(
            1
            for item in questions
            if answers.get(item.id, "").upper() == item.correct_option.upper()
        )
        result = QuizResult(
            self.repos.results.create_id(),
            int(quiz_id),
            score,
            len(questions),
            round(score / len(questions) * 100, 1),
            max(0, int(duration_seconds)),
            now_iso(),
        )
        return self.repos.results.add(result)

    def delete_quiz(self, quiz_id: int) -> None:
        for item in self.repos.questions.all():
            if item.quiz_id == int(quiz_id):
                self.repos.questions.delete(item.id)
        for item in self.repos.results.all():
            if item.quiz_id == int(quiz_id):
                self.repos.results.delete(item.id)
        self.repos.quizzes.delete(quiz_id)

    def load_demo(self) -> None:
        load_demo_data(self.repos)

    def reset(self) -> None:
        for name, fields in SCHEMAS.items():
            self.repos.data_dir.joinpath(f"{name}.csv").unlink(missing_ok=True)
        self.repos = RepositoryBundle(self.repos.data_dir)

    def export(self, name: str) -> Path:
        mapping = {
            "Tasks": "tasks",
            "Study History": "study_sessions",
            "Quiz Results": "quiz_results",
        }
        source_name = mapping.get(name)
        if not source_name:
            raise ValidationError("Unknown export type.")
        rows = getattr(
            self.repos,
            {"study_sessions": "sessions", "quiz_results": "results"}.get(
                source_name, source_name
            ),
        ).storage.read_all()
        destination = (
            self.export_dir / f"{source_name}_{datetime.now():%Y%m%d_%H%M%S}.csv"
        )
        with destination.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                file, fieldnames=SCHEMAS[source_name], quoting=csv.QUOTE_ALL
            )
            writer.writeheader()
            writer.writerows(rows)
        return destination

    def _require_subject(self, subject_id: int) -> Subject:
        return self._require(self.repos.subjects.get(subject_id), "Subject")

    @staticmethod
    def _require(value, label: str):
        if value is None:
            raise ValidationError(f"{label} was not found.")
        return value

    @staticmethod
    def _choice(value: str, choices: set[str], label: str) -> str:
        value = str(value).upper()
        if value not in choices:
            raise ValidationError(f"{label} is invalid.")
        return value
