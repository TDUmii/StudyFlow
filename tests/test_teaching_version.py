from pathlib import Path

from PySide6.QtWidgets import QApplication

import teaching.main as simple
from teaching.csv_helper import next_id, read_csv, write_csv


def use_temp_data(monkeypatch, tmp_path):
    monkeypatch.setattr(simple, "DATA_DIR", tmp_path)
    monkeypatch.setattr(simple, "SUBJECT_FILE", tmp_path / "subjects.csv")
    monkeypatch.setattr(simple, "TASK_FILE", tmp_path / "tasks.csv")
    monkeypatch.setattr(simple, "SETTING_FILE", tmp_path / "settings.csv")


def test_simple_csv_functions_preserve_vietnamese_and_new_lines(tmp_path):
    path = tmp_path / "notes.csv"
    fields = ["id", "content"]
    rows = [{"id": "1", "content": 'Tiếng Việt, có "dấu"\nvà dòng mới'}]

    write_csv(path, fields, rows)

    assert read_csv(path, fields) == rows
    assert next_id(rows) == 2


def test_simple_app_can_add_subject_and_task(monkeypatch, tmp_path):
    use_temp_data(monkeypatch, tmp_path)
    app = QApplication.instance() or QApplication([])
    window = simple.StudyFlowSimple()

    math_index = window.subject_library.findData("mathematics")
    window.subject_library.setCurrentIndex(math_index)
    window.add_subject()

    window.task_title.setText("Làm bài tập đại số")
    window.add_task()

    subjects = read_csv(simple.SUBJECT_FILE, simple.SUBJECT_FIELDS)
    tasks = read_csv(simple.TASK_FILE, simple.TASK_FIELDS)
    assert subjects[0]["key"] == "mathematics"
    assert tasks[0]["title"] == "Làm bài tập đại số"
    assert window.subject_table.item(0, 1).text() == "Toán học"
    assert "Toán học" in window.recommendation.text()

    window.close()
    app.processEvents()


def test_simple_app_language_and_data_persist(monkeypatch, tmp_path):
    use_temp_data(monkeypatch, tmp_path)
    app = QApplication.instance() or QApplication([])
    first = simple.StudyFlowSimple()
    first.subject_library.setCurrentIndex(first.subject_library.findData("mathematics"))
    first.add_subject()
    first.change_language("en")
    first.close()

    second = simple.StudyFlowSimple()
    assert second.language == "en"
    assert second.subject_table.item(0, 1).text() == "Mathematics"
    assert second.tabs.count() == 3
    second.close()
    app.processEvents()


def test_teaching_files_stay_small_and_focused():
    teaching_dir = Path("teaching")
    source_files = sorted(teaching_dir.glob("*.py"))
    assert {path.name for path in source_files} == {
        "__init__.py",
        "csv_helper.py",
        "main.py",
        "translations.py",
    }
    assert len(source_files) == 4
    assert (
        len((teaching_dir / "csv_helper.py").read_text(encoding="utf-8").splitlines())
        < 80
    )
