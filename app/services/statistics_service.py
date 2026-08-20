from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from app.repositories import RepositoryBundle


class StatisticsService:
    def __init__(self, repos: RepositoryBundle):
        self.repos = repos

    def summary(self) -> dict[str, object]:
        tasks = self.repos.tasks.all()
        sessions = self.repos.sessions.all()
        results = self.repos.results.all()
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        weekly_sessions = [
            s
            for s in sessions
            if s.status == "COMPLETED" and s.date >= week_start.isoformat()
        ]
        weekly_tasks = [t for t in tasks if t.created_at[:10] >= week_start.isoformat()]
        completed_week = sum(t.status == "COMPLETED" for t in weekly_tasks)
        averages = [r.accuracy for r in results]
        by_subject: dict[int, int] = defaultdict(int)
        by_day: dict[str, int] = defaultdict(int)
        for session in sessions:
            if session.status == "COMPLETED":
                by_subject[session.subject_id] += session.actual_minutes
                by_day[session.date] += session.actual_minutes
        subjects = {s.id: s.name for s in self.repos.subjects.all()}
        most_id = max(by_subject, key=by_subject.get) if by_subject else None
        return {
            "tasks_today": sum(
                t.deadline == today.isoformat() and t.status != "COMPLETED"
                for t in tasks
            ),
            "upcoming": sum(
                today.isoformat()
                < t.deadline
                <= (today + timedelta(days=7)).isoformat()
                and t.status != "COMPLETED"
                for t in tasks
            ),
            "study_minutes": sum(s.actual_minutes for s in weekly_sessions),
            "completed_tasks": completed_week,
            "weekly_tasks": len(weekly_tasks),
            "average_quiz": (
                round(sum(averages) / len(averages), 1) if averages else 0.0
            ),
            "streak": self.streak(by_day),
            "most_studied": subjects.get(most_id, "—"),
            "by_subject": {
                subjects.get(key, "Unknown"): value for key, value in by_subject.items()
            },
            "by_day": dict(by_day),
            "flashcard_accuracy": self.flashcard_accuracy(),
        }

    @staticmethod
    def streak(by_day: dict[str, int]) -> int:
        cursor = date.today()
        streak = 0
        if by_day and cursor.isoformat() not in by_day:
            cursor -= timedelta(days=1)
        while by_day.get(cursor.isoformat(), 0) > 0:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def flashcard_accuracy(self) -> float:
        cards = self.repos.flashcards.all()
        correct = sum(c.correct_count for c in cards)
        total = correct + sum(c.wrong_count for c in cards)
        return round(correct / total * 100, 1) if total else 0.0
