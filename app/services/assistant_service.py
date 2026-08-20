from __future__ import annotations

from app.repositories import RepositoryBundle
from .recommendation_service import RecommendationService


class AssistantService:
    def __init__(self, repos: RepositoryBundle):
        self.engine = RecommendationService(repos)

    def recommendations(self) -> list[dict[str, object]]:
        return self.engine.scores()

    def message(self) -> str:
        ranked = self.recommendations()
        if not ranked:
            return "There is not enough study data yet.\n\nAdd subjects, tasks, study sessions or quiz results to receive personalized recommendations."
        top = ranked[0]
        if not top["reasons"]:
            return f'{top["subject"]} is ready for your next study session. Add a task or quiz result to receive a more specific recommendation.'
        reasons = "\n".join(f"• {reason}" for reason in top["reasons"])
        minutes = min(60, max(20, round(int(top["score"]) / 10) * 5))
        return f'{top["subject"]}\n\nPriority Score: {top["score"]}\n\nWhy?\n{reasons}\n\nRecommendation:\nStudy {top["subject"]} for approximately {minutes} minutes today.'

    def study_plan(self, minutes: int):
        return self.engine.study_plan(minutes)
