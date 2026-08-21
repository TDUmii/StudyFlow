"""Language registry.

Add a language module and one entry here to make it available throughout the app.
"""

from app.i18n.en import TRANSLATIONS as ENGLISH
from app.i18n.vi import TRANSLATIONS as VIETNAMESE

DEFAULT_LANGUAGE = "en"

SUPPORTED_LANGUAGES = {
    "en": {
        "name": "English",
        "native_name": "English",
        "translations": ENGLISH,
    },
    "vi": {
        "name": "Vietnamese",
        "native_name": "Tiếng Việt",
        "translations": VIETNAMESE,
    },
}
