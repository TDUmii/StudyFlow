from datetime import date

from app.services.statistics_service import StatisticsService


def test_statistics_aggregation(service):
    subject = service.create_subject("Python")
    session = service.create_session(subject.id, date.today().isoformat(), "18:00", 30)
    service.complete_session(session.id, 45)
    quiz = service.create_quiz(
        subject.id,
        "Quiz",
        "",
        [
            {
                "question_text": "Q",
                "option_a": "A",
                "option_b": "B",
                "option_c": "C",
                "option_d": "D",
                "correct_option": "A",
                "explanation": "",
            }
        ],
    )
    q = service.repos.questions.all()[0]
    service.submit_quiz(quiz.id, {q.id: "A"})
    card = service.create_flashcard(subject.id, "Q", "A")
    service.review_flashcard(card.id, "GOOD")
    stats = StatisticsService(service.repos).summary()
    assert stats["study_minutes"] == 45
    assert stats["average_quiz"] == 100
    assert stats["flashcard_accuracy"] == 100
    assert stats["streak"] == 1
