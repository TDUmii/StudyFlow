from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from app.i18n.config import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES


class LanguageManager(QObject):
    """Stores the active language and broadcasts runtime language changes."""

    language_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._language = DEFAULT_LANGUAGE

    @property
    def current_language(self) -> str:
        return self._language

    def set_language(self, language_code: str, *, emit: bool = True) -> bool:
        if language_code not in SUPPORTED_LANGUAGES:
            language_code = DEFAULT_LANGUAGE
        if language_code == self._language:
            return False
        self._language = language_code
        if emit:
            self.language_changed.emit(language_code)
        return True

    def translate(self, key: str, **values: object) -> str:
        active = SUPPORTED_LANGUAGES[self._language]["translations"]
        fallback = SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE]["translations"]
        template = active.get(key, fallback.get(key, key))
        try:
            return template.format(**values)
        except (KeyError, ValueError):
            return template


language_manager = LanguageManager()


def tr(key: str, **values: object) -> str:
    return language_manager.translate(key, **values)
