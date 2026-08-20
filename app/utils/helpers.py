from __future__ import annotations


def next_id(rows: list[dict[str, str]]) -> int:
    ids: list[int] = []
    for row in rows:
        try:
            ids.append(int(row["id"]))
        except (KeyError, TypeError, ValueError):
            continue
    return max(ids, default=0) + 1


def safe_int(value: object, default: int = 0) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default
