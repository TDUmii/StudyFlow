from datetime import date, timedelta

import pytest

from app.services.assistant_service import AssistantService


def test_overdue_scores_above_future_task(service):
    urgent = service.create_subject("Urgent")
    future = service.create_subject("Future")
    service.create_task(
        "Overdue", urgent.id, (date.today() - timedelta(days=1)).isoformat(), "HIGH", 30
    )
    service.create_task(
        "Later", future.id, (date.today() + timedelta(days=10)).isoformat(), "LOW", 30
    )
    scores = {
        x["subject"]: x["score"]
        for x in AssistantService(service.repos).recommendations()
    }
    assert scores["Urgent"] > scores["Future"]


@pytest.mark.parametrize("available", [30, 60, 90, 120])
def test_study_plan_never_exceeds_available_time(service, available):
    for name in ("Math", "Python", "English"):
        subject = service.create_subject(name)
        service.create_task(name, subject.id, date.today().isoformat(), "HIGH", 30)
    plan = AssistantService(service.repos).study_plan(available)
    assert sum(x["minutes"] for x in plan) <= available
    assert all(x["minutes"] >= 10 for x in plan)
