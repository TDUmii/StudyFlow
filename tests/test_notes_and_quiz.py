def test_multiline_note_survives_repository_reload(service):
    subject = service.create_subject("Ngữ văn")
    content = 'Dòng một, có phẩy và "trích dẫn".\nDòng hai: tiếng Việt.'
    note = service.create_note("Ghi chú", subject.id, content)
    assert service.repos.notes.get(note.id).content == content


def test_quiz_submission_and_review_data(service):
    subject = service.create_subject("Python")
    quiz = service.create_quiz(
        subject.id,
        "Basics",
        "",
        [
            {
                "question_text": "2 + 2?",
                "option_a": "3",
                "option_b": "4",
                "option_c": "5",
                "option_d": "6",
                "correct_option": "B",
                "explanation": "Addition",
            }
        ],
    )
    question = service.repos.questions.all()[0]
    result = service.submit_quiz(quiz.id, {question.id: "B"}, 12)
    assert (result.score, result.total, result.accuracy) == (1, 1, 100.0)
    service.delete_quiz(quiz.id)
    assert not service.repos.questions.all() and not service.repos.results.all()
