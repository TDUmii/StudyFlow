from __future__ import annotations

from datetime import date, timedelta

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
from app.utils.dates import now_iso


def load_demo_data(repos) -> None:
    for repo in (
        repos.subjects,
        repos.tasks,
        repos.sessions,
        repos.notes,
        repos.flashcards,
        repos.quizzes,
        repos.questions,
        repos.results,
    ):
        repo.clear()
    now = now_iso()
    today = date.today()
    repos.profile.save("Minh", now)
    repos.settings.set("default_study_duration", "30")
    repos.settings.set("theme", "light")
    repos.settings.set("minimum_study_day", "10")
    subjects = [
        (1, "Mathematics", "mathematics", "#6366F1", 80),
        (2, "Python", "python", "#22C55E", 90),
        (3, "English", "english", "#F59E0B", 85),
        (4, "Physics", "physics", "#EF4444", 80),
    ]
    for i, name, catalog_key, color, target in subjects:
        repos.subjects.add(
            Subject(i, name, color, f"{name} learning goals", target, now, catalog_key)
        )
    task_titles = [
        "Algebra worksheet",
        "Build CSV exercise",
        "Vocabulary review",
        "Motion problems",
        "Prepare math quiz",
        "Refactor Python class",
        "Read English article",
        "Physics lab notes",
    ]
    for index, title in enumerate(task_titles, 1):
        deadline = (
            today + timedelta(days=(-1, 0, 1, 2, 4, 6, 8, 10)[index - 1])
        ).isoformat()
        status = (
            "COMPLETED" if index in (3, 6) else "IN_PROGRESS" if index == 2 else "TODO"
        )
        repos.tasks.add(
            Task(
                index,
                title,
                "Demo task",
                ((index - 1) % 4) + 1,
                deadline,
                ("HIGH", "MEDIUM", "LOW")[index % 3],
                25 + index * 5,
                status,
                now,
                now if status == "COMPLETED" else "",
            )
        )
    for index in range(1, 8):
        session_date = (today - timedelta(days=7 - index)).isoformat()
        subject_id = ((index - 1) % 4) + 1
        repos.sessions.add(
            StudySession(
                index,
                subject_id,
                str(index) if index <= 4 else "",
                session_date,
                "18:00",
                30,
                20 + index * 4,
                "Demo study session",
                "COMPLETED",
                now,
            )
        )
    for index in range(1, 11):
        repos.flashcards.add(
            Flashcard(
                index,
                ((index - 1) % 4) + 1,
                f"Demo question {index}?",
                f"Demo answer {index}",
                "HARD" if index % 3 == 0 else "GOOD",
                index % 4 + 1,
                index % 3,
                (today - timedelta(days=index)).isoformat(),
                now,
            )
        )
    for index in range(1, 6):
        repos.notes.add(
            Note(
                index,
                f"Study note {index}",
                ((index - 1) % 4) + 1,
                f'A useful note, with commas, quotes "like this", and detail #{index}.\nSecond line for CSV testing.',
                now,
                now,
            )
        )
    for quiz_id, (subject_id, title) in enumerate(
        ((1, "Algebra Check"), (2, "Python Basics"), (3, "English Review")), 1
    ):
        repos.quizzes.add(Quiz(quiz_id, subject_id, title, "Demo quiz", now))
    qid = 1
    for quiz_id in range(1, 4):
        for number in range(1, 5):
            repos.questions.add(
                QuizQuestion(
                    qid,
                    quiz_id,
                    f"Question {number} for quiz {quiz_id}?",
                    "Answer A",
                    "Answer B",
                    "Answer C",
                    "Answer D",
                    ("A", "B", "C", "D")[number - 1],
                    "Review the lesson notes.",
                )
            )
            qid += 1
    for rid, (quiz_id, score) in enumerate(((1, 2), (2, 4), (3, 3)), 1):
        repos.results.add(
            QuizResult(rid, quiz_id, score, 4, score / 4 * 100, 120 + rid * 20, now)
        )
