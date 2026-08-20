from app.services.assistant_service import AssistantService


def test_demo_data_populates_every_required_area(service):
    service.load_demo()
    r = service.repos
    assert (
        len(r.subjects.all()) >= 4
        and len(r.tasks.all()) >= 8
        and len(r.sessions.all()) >= 7
    )
    assert (
        len(r.flashcards.all()) >= 10
        and len(r.quizzes.all()) >= 3
        and len(r.questions.all()) >= 10
        and len(r.results.all()) >= 3
        and len(r.notes.all()) >= 5
    )
    assert AssistantService(r).recommendations()
