from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from app.repositories import RepositoryBundle
from app.i18n import tr
from app.data.subject_catalog import subject_display_name


class RecommendationService:
    def __init__(self, repos: RepositoryBundle):
        self.repos = repos

    def scores(self) -> list[dict[str, object]]:
        today = date.today()
        subjects = self.repos.subjects.all()
        scores = {s.id: 0 for s in subjects}
        reasons: dict[int, list[str]] = defaultdict(list)
        for task in self.repos.tasks.all():
            if task.status == "COMPLETED":
                continue
            try:
                days = (date.fromisoformat(task.deadline) - today).days
            except ValueError:
                continue
            points = (
                35
                if days < 0
                else 28 if days == 0 else 22 if days == 1 else 12 if days <= 7 else 3
            )
            if task.priority == "HIGH":
                points += 12
            scores[task.subject_id] = scores.get(task.subject_id, 0) + points
            if days < 0:
                reasons[task.subject_id].append(tr("reason.overdue", title=task.title))
            elif days <= 1:
                reason_key = "reason.due_today" if days == 0 else "reason.due_tomorrow"
                reasons[task.subject_id].append(tr(reason_key, title=task.title))
        quiz_by_subject: dict[int, list[float]] = defaultdict(list)
        quizzes = {q.id: q for q in self.repos.quizzes.all()}
        for result in self.repos.results.all():
            quiz = quizzes.get(result.quiz_id)
            if quiz:
                quiz_by_subject[quiz.subject_id].append(result.accuracy)
        for subject_id, values in quiz_by_subject.items():
            average = sum(values) / len(values)
            if average < 70:
                scores[subject_id] += int((70 - average) * 0.7) + 10
                reasons[subject_id].append(
                    tr("reason.quiz_average", average=f"{average:.0f}")
                )
        for card in self.repos.flashcards.all():
            attempts = card.correct_count + card.wrong_count
            if attempts and card.correct_count / attempts < 0.7:
                scores[card.subject_id] += 8
                reasons[card.subject_id].append(tr("reason.flashcards"))
            if (
                not card.last_reviewed
                or card.last_reviewed < (today - timedelta(days=7)).isoformat()
            ):
                scores[card.subject_id] += 3
        week = (today - timedelta(days=6)).isoformat()
        minutes: dict[int, int] = defaultdict(int)
        for session in self.repos.sessions.all():
            if session.status == "COMPLETED" and session.date >= week:
                minutes[session.subject_id] += session.actual_minutes
        for subject in subjects:
            if minutes[subject.id] < 30:
                scores[subject.id] += 10
                reasons[subject.id].append(
                    tr("reason.low_activity", minutes=minutes[subject.id])
                )
        return sorted(
            (
                {
                    "subject_id": subject.id,
                    "subject": subject_display_name(subject),
                    "score": min(scores.get(subject.id, 0), 100),
                    "reasons": list(dict.fromkeys(reasons[subject.id]))[:4],
                }
                for subject in subjects
            ),
            key=lambda item: (-int(item["score"]), str(item["subject"])),
        )

    def study_plan(self, available_minutes: int) -> list[dict[str, object]]:
        available_minutes = max(0, int(available_minutes))
        ranked = [item for item in self.scores() if item["score"] > 0]
        if not ranked or available_minutes < 10:
            return []
        count = min(len(ranked), max(1, available_minutes // 15))
        selected = ranked[:count]
        weights = [max(1, int(item["score"])) for item in selected]
        total_weight = sum(weights)
        remaining = available_minutes
        plan = []
        for index, (item, weight) in enumerate(zip(selected, weights)):
            minutes = (
                remaining
                if index == len(selected) - 1
                else max(10, round(available_minutes * weight / total_weight / 5) * 5)
            )
            minutes = min(minutes, remaining)
            remaining -= minutes
            plan.append({**item, "minutes": minutes})
        return [item for item in plan if item["minutes"] > 0]
