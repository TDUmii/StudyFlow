from __future__ import annotations

from app.repositories import RepositoryBundle
from app.i18n import tr
from .recommendation_service import RecommendationService


class AssistantService:
    def __init__(self, repos: RepositoryBundle):
        self.engine = RecommendationService(repos)

    def recommendations(self) -> list[dict[str, object]]:
        return self.engine.scores()

    def message(self) -> str:
        ranked = self.recommendations()
        if not ranked:
            return tr("assistant.not_enough")
        top = ranked[0]
        if not top["reasons"]:
            return tr("assistant.ready", subject=top["subject"])
        reasons = "\n".join(f"• {reason}" for reason in top["reasons"])
        minutes = min(60, max(20, round(int(top["score"]) / 10) * 5))
        return tr(
            "assistant.message",
            subject=top["subject"],
            score=top["score"],
            reasons=reasons,
            minutes=minutes,
        )

    def study_plan(self, minutes: int):
        return self.engine.study_plan(minutes)
