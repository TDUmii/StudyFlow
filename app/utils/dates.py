from __future__ import annotations

from datetime import date, datetime


def today_iso() -> str:
    return date.today().isoformat()


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def display_date(value: str) -> str:
    parsed = parse_date(value)
    return parsed.strftime("%d/%m/%Y") if parsed else "—"


def to_iso_date(value: str) -> str:
    return datetime.strptime(value.strip(), "%d/%m/%Y").date().isoformat()
