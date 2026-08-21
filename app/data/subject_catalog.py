"""Built-in subject library and localized subject-name helpers."""

from __future__ import annotations

from dataclasses import dataclass

from app.i18n import SUPPORTED_LANGUAGES, language_manager, tr


@dataclass(frozen=True)
class SubjectDefinition:
    key: str
    translation_key: str
    color: str


SUBJECT_CATALOG = (
    SubjectDefinition("mathematics", "subject.mathematics", "#6366F1"),
    SubjectDefinition("literature", "subject.literature", "#EC4899"),
    SubjectDefinition("english", "subject.english", "#F59E0B"),
    SubjectDefinition("physics", "subject.physics", "#EF4444"),
    SubjectDefinition("chemistry", "subject.chemistry", "#14B8A6"),
    SubjectDefinition("biology", "subject.biology", "#22C55E"),
    SubjectDefinition("history", "subject.history", "#A16207"),
    SubjectDefinition("geography", "subject.geography", "#0EA5E9"),
    SubjectDefinition("informatics", "subject.informatics", "#8B5CF6"),
    SubjectDefinition("technology", "subject.technology", "#64748B"),
    SubjectDefinition("civic_education", "subject.civic_education", "#F97316"),
    SubjectDefinition("physical_education", "subject.physical_education", "#10B981"),
    SubjectDefinition("music", "subject.music", "#D946EF"),
    SubjectDefinition("fine_arts", "subject.fine_arts", "#FB7185"),
    SubjectDefinition("python", "subject.python", "#22C55E"),
)

CATALOG_BY_KEY = {item.key: item for item in SUBJECT_CATALOG}


def catalog_name(key: str) -> str:
    definition = CATALOG_BY_KEY.get(str(key))
    return tr(definition.translation_key) if definition else ""


def catalog_name_for_language(key: str, language_code: str) -> str:
    definition = CATALOG_BY_KEY.get(str(key))
    if not definition:
        return ""
    translations = SUPPORTED_LANGUAGES.get(language_code, SUPPORTED_LANGUAGES["en"])[
        "translations"
    ]
    return translations.get(definition.translation_key, definition.key)


def infer_catalog_key(name: str) -> str:
    """Recognize legacy built-in names saved before catalog keys existed."""
    candidate = str(name).strip().casefold()
    if not candidate:
        return ""
    for definition in SUBJECT_CATALOG:
        for language in SUPPORTED_LANGUAGES.values():
            translated = language["translations"].get(definition.translation_key, "")
            if translated.casefold() == candidate:
                return definition.key
    aliases = {"math": "mathematics", "computer science": "informatics"}
    return aliases.get(candidate, "")


def subject_catalog_key(subject) -> str:
    return (
        subject.catalog_key
        if subject.catalog_key in CATALOG_BY_KEY
        else infer_catalog_key(subject.name)
    )


def subject_display_name(subject, language_code: str | None = None) -> str:
    key = subject_catalog_key(subject)
    if key:
        definition = CATALOG_BY_KEY[key]
        language = language_code or language_manager.current_language
        return catalog_name_for_language(key, language) or subject.name
    if (language_code or language_manager.current_language) == "vi" and subject.name_vi:
        return subject.name_vi
    return subject.name


def subject_search_text(subject) -> str:
    """Search matches either language, even when only one is currently visible."""
    return " ".join(
        {
            subject.name,
            subject.name_vi,
            subject_display_name(subject, "en"),
            subject_display_name(subject, "vi"),
            subject.description,
        }
    )


def catalog_options() -> list[tuple[str, str, str]]:
    return [(item.key, catalog_name(item.key), item.color) for item in SUBJECT_CATALOG]
