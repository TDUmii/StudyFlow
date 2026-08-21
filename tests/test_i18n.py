import os
import ast
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.i18n import SUPPORTED_LANGUAGES, language_manager, tr
from app.services import AppService
from app.services.assistant_service import AssistantService
from app.ui.main_window import MainWindow


def test_language_files_have_matching_keys():
    english = set(SUPPORTED_LANGUAGES["en"]["translations"])
    vietnamese = set(SUPPORTED_LANGUAGES["vi"]["translations"])
    assert english == vietnamese
    assert len(english) >= 180


def test_every_translation_key_used_by_code_exists():
    used_keys = set()
    for path in Path("app").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "tr"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                used_keys.add(node.args[0].value)
    available = set(SUPPORTED_LANGUAGES["en"]["translations"])
    assert used_keys <= available


def test_translation_switch_and_fallback():
    language_manager.set_language("en", emit=False)
    assert tr("nav.dashboard") == "Dashboard"
    language_manager.set_language("vi", emit=False)
    assert tr("nav.dashboard") == "Tổng quan"
    assert tr("subjects.delete_message", name="Toán").startswith('Xóa "Toán"')
    assert tr("missing.translation.key") == "missing.translation.key"
    language_manager.set_language("unsupported", emit=False)
    assert language_manager.current_language == "en"


def test_language_setting_persists(service):
    service.setup_profile("Minh", 30, "vi")
    reloaded = AppService(service.repos.data_dir, service.export_dir)
    assert reloaded.repos.settings.get("language") == "vi"
    reloaded.reset()
    assert reloaded.repos.settings.get("language") == "vi"


def test_live_window_switch_rebuilds_current_page(service):
    app = QApplication.instance() or QApplication([])
    language_manager.set_language("en", emit=False)
    window = MainWindow(service)
    window.show_page(9)
    service.repos.settings.set("language", "vi")
    language_manager.set_language("vi")
    app.processEvents()

    assert window.windowTitle() == "StudyFlow — Trợ lý học tập cá nhân"
    assert window.nav_buttons[0].text() == "Tổng quan"
    assert window.nav_buttons[-1].text() == "Cài đặt"
    assert window.stack.currentIndex() == 9
    assert window.pages[-1].language.currentData() == "vi"

    window.close()
    language_manager.set_language("en", emit=False)


def test_smart_assistant_uses_active_language(service):
    service.load_demo()
    language_manager.set_language("vi", emit=False)
    message = AssistantService(service.repos).message()
    assert "Điểm ưu tiên" in message
    assert "Gợi ý" in message
    language_manager.set_language("en", emit=False)
