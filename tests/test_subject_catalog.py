import csv

import pytest
from PySide6.QtWidgets import QApplication

from app.data.subject_catalog import SUBJECT_CATALOG, subject_display_name
from app.i18n import SUPPORTED_LANGUAGES, language_manager
from app.services.assistant_service import AssistantService
from app.storage.csv_storage import CSVStorage
from app.ui.dialogs.forms import SubjectDialog
from app.ui.main_window import MainWindow
from app.utils.validators import ValidationError


def test_catalog_contains_common_school_subjects():
    keys = {item.key for item in SUBJECT_CATALOG}
    assert {
        "mathematics",
        "literature",
        "english",
        "physics",
        "chemistry",
        "biology",
        "history",
        "geography",
        "informatics",
    } <= keys
    for item in SUBJECT_CATALOG:
        assert item.translation_key in SUPPORTED_LANGUAGES["en"]["translations"]
        assert item.translation_key in SUPPORTED_LANGUAGES["vi"]["translations"]


def test_catalog_subject_switches_language_everywhere(service):
    subject = service.create_subject(catalog_key="mathematics")

    language_manager.set_language("vi", emit=False)
    assert subject_display_name(subject) == "Toán học"
    assert AssistantService(service.repos).recommendations()[0]["subject"] == "Toán học"

    language_manager.set_language("en", emit=False)
    assert subject_display_name(subject) == "Mathematics"


def test_legacy_builtin_name_is_localized_without_data_loss(service):
    subject = service.create_subject("Physics")
    language_manager.set_language("vi", emit=False)
    assert subject_display_name(subject) == "Vật lý"
    language_manager.set_language("en", emit=False)
    assert subject_display_name(subject) == "Physics"


def test_custom_subject_keeps_separate_english_and_vietnamese_names(service):
    subject = service.create_subject("Robotics", name_vi="Rô-bốt học")
    language_manager.set_language("vi", emit=False)
    assert subject_display_name(subject) == "Rô-bốt học"
    language_manager.set_language("en", emit=False)
    assert subject_display_name(subject) == "Robotics"


def test_catalog_prevents_duplicate_legacy_subject(service):
    service.create_subject("Mathematics")
    with pytest.raises(ValidationError):
        service.create_subject(catalog_key="mathematics")


def test_subject_dialog_offers_library_and_bilingual_custom_fields():
    app = QApplication.instance() or QApplication([])
    language_manager.set_language("vi", emit=False)
    dialog = SubjectDialog()

    math_index = dialog.catalog.findData("mathematics")
    assert math_index > 0
    assert dialog.catalog.itemText(math_index) == "Toán học"
    dialog.catalog.setCurrentIndex(math_index)
    assert not dialog.name.isEnabled()
    assert dialog.values()["catalog_key"] == "mathematics"

    dialog.catalog.setCurrentIndex(0)
    assert dialog.name.isEnabled() and dialog.name_vi.isEnabled()
    dialog.name.setText("Robotics")
    dialog.name_vi.setText("Rô-bốt học")
    dialog.validate()
    assert dialog.values()["name_vi"] == "Rô-bốt học"
    dialog.close()
    language_manager.set_language("en", emit=False)
    app.processEvents()


def test_vietnamese_window_never_displays_builtin_english_subject_name(service):
    app = QApplication.instance() or QApplication([])
    service.load_demo()
    language_manager.set_language("vi", emit=False)
    window = MainWindow(service)
    app.processEvents()

    subjects_page = window.pages[2]
    assistant_page = window.pages[8]
    visible_subjects = {
        subjects_page.table.item(row, 1).text()
        for row in range(subjects_page.table.rowCount())
    }
    assert "Toán học" in visible_subjects
    assert "Mathematics" not in visible_subjects
    assert "Toán học" in assistant_page.message.toPlainText()
    assert "Mathematics" not in assistant_page.message.toPlainText()

    window.close()
    language_manager.set_language("en", emit=False)


def test_csv_header_migration_preserves_existing_subject(tmp_path):
    path = tmp_path / "subjects.csv"
    old_fields = [
        "id",
        "name",
        "color",
        "description",
        "target_score",
        "created_at",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=old_fields)
        writer.writeheader()
        writer.writerow(
            {
                "id": "1",
                "name": "Mathematics",
                "color": "#6366F1",
                "description": "Legacy data",
                "target_score": "80",
                "created_at": "2026-08-20T10:00:00",
            }
        )

    new_fields = [*old_fields, "catalog_key", "name_vi"]
    storage = CSVStorage(path, new_fields)
    rows = storage.read_all()

    assert rows[0]["name"] == "Mathematics"
    assert rows[0]["description"] == "Legacy data"
    assert rows[0]["catalog_key"] == ""
    assert rows[0]["name_vi"] == ""
    assert path.read_text(encoding="utf-8").splitlines()[0] == ",".join(
        f'"{field}"' for field in new_fields
    )
