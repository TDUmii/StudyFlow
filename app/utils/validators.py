from __future__ import annotations

from app.utils.dates import parse_date
from app.i18n import tr


class ValidationError(ValueError):
    pass


def required(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError(tr("validation.required", label=label))
    return cleaned


def integer_between(value: object, minimum: int, maximum: int, label: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(tr("validation.number", label=label)) from exc
    if not minimum <= number <= maximum:
        raise ValidationError(
            tr("validation.range", label=label, minimum=minimum, maximum=maximum)
        )
    return number


def iso_date(value: str, label: str | None = None) -> str:
    label = label or tr("field.date")
    if not parse_date(value):
        raise ValidationError(tr("validation.valid_date", label=label))
    return value
