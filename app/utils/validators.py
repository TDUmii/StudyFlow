from __future__ import annotations

from app.utils.dates import parse_date


class ValidationError(ValueError):
    pass


def required(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError(f"{label} is required.")
    return cleaned


def integer_between(value: object, minimum: int, maximum: int, label: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{label} must be a number.") from exc
    if not minimum <= number <= maximum:
        raise ValidationError(f"{label} must be between {minimum} and {maximum}.")
    return number


def iso_date(value: str, label: str = "Date") -> str:
    if not parse_date(value):
        raise ValidationError(f"{label} must be a valid date.")
    return value
