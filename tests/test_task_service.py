from datetime import date

import pytest

from app.utils.validators import ValidationError


def test_task_crud_completion_and_persistence(service):
    subject = service.create_subject("Toán")
    task = service.create_task(
        "Bài tập, chương 1",
        subject.id,
        date.today().isoformat(),
        "HIGH",
        40,
        'Có dấu "ngoặc"',
    )
    assert service.repos.tasks.get(task.id).title == "Bài tập, chương 1"
    service.update_task(
        task.id,
        title="Bài tập mới",
        subject_id=subject.id,
        deadline=task.deadline,
        priority="LOW",
        minutes=25,
        description="updated",
    )
    service.set_task_status(task.id, "COMPLETED")
    assert service.repos.tasks.get(task.id).status == "COMPLETED"
    service.repos.tasks.delete(task.id)
    assert service.repos.tasks.get(task.id) is None


@pytest.mark.parametrize(
    "deadline,minutes",
    [
        ("not-a-date", 30),
        (date.today().isoformat(), 0),
        (date.today().isoformat(), 601),
    ],
)
def test_invalid_task_data(service, deadline, minutes):
    subject = service.create_subject("Math")
    with pytest.raises(ValidationError):
        service.create_task("Task", subject.id, deadline, "HIGH", minutes)


def test_missing_subject_and_relationship_guard(service):
    with pytest.raises(ValidationError):
        service.create_task("Task", 99, date.today().isoformat(), "HIGH", 20)
    subject = service.create_subject("Physics")
    service.create_task("Task", subject.id, date.today().isoformat(), "LOW", 20)
    with pytest.raises(ValidationError):
        service.delete_subject(subject.id)
