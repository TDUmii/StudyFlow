"""Small, teachable and safe CSV persistence layer."""

from __future__ import annotations

import csv
import logging
import os
from pathlib import Path
from typing import Iterable

LOGGER = logging.getLogger(__name__)


class StorageError(RuntimeError):
    """A user-facing storage failure without leaking a raw traceback."""


class CSVStorage:
    def __init__(self, file_path: Path | str, fieldnames: list[str]):
        self.file_path = Path(file_path)
        self.fieldnames = list(fieldnames)
        self.ensure_file()

    def ensure_file(self) -> None:
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.file_path.exists() or self.file_path.stat().st_size == 0:
                self._write_file(self.file_path, [])
        except OSError as exc:
            raise StorageError(f"Could not prepare {self.file_path.name}.") from exc

    def read_all(self) -> list[dict[str, str]]:
        self.ensure_file()
        rows: list[dict[str, str]] = []
        try:
            with self.file_path.open("r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)
                if reader.fieldnames != self.fieldnames:
                    LOGGER.warning(
                        "Unexpected header in %s; expected %s",
                        self.file_path.name,
                        self.fieldnames,
                    )
                for line_number, row in enumerate(reader, start=2):
                    if row is None or None in row:
                        LOGGER.warning(
                            "Skipped malformed row %s in %s",
                            line_number,
                            self.file_path.name,
                        )
                        continue
                    cleaned = {
                        field: (row.get(field) or "") for field in self.fieldnames
                    }
                    if any(cleaned.values()):
                        rows.append(cleaned)
        except (OSError, csv.Error) as exc:
            raise StorageError(f"Could not read {self.file_path.name}.") from exc
        return rows

    def append(self, row: dict[str, object]) -> None:
        normalized = self._normalize(row)
        try:
            with self.file_path.open("a", encoding="utf-8", newline="") as file:
                csv.DictWriter(
                    file, fieldnames=self.fieldnames, quoting=csv.QUOTE_ALL
                ).writerow(normalized)
        except (OSError, csv.Error) as exc:
            raise StorageError(f"Could not save to {self.file_path.name}.") from exc

    def write_all(self, rows: Iterable[dict[str, object]]) -> None:
        """Write a temporary file first, then atomically replace the original."""
        temporary = self.file_path.with_suffix(self.file_path.suffix + ".tmp")
        try:
            self._write_file(temporary, rows)
            os.replace(temporary, self.file_path)
        except (OSError, csv.Error) as exc:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise StorageError(f"Could not update {self.file_path.name}.") from exc

    def update(
        self, record_id: str | int, new_data: dict[str, object], id_field: str = "id"
    ) -> bool:
        rows = self.read_all()
        changed = False
        for row in rows:
            if row.get(id_field) == str(record_id):
                row.update(
                    {
                        key: str(value)
                        for key, value in new_data.items()
                        if key in self.fieldnames
                    }
                )
                changed = True
                break
        if changed:
            self.write_all(rows)
        return changed

    def delete(self, record_id: str | int, id_field: str = "id") -> bool:
        rows = self.read_all()
        remaining = [row for row in rows if row.get(id_field) != str(record_id)]
        if len(remaining) == len(rows):
            return False
        self.write_all(remaining)
        return True

    def _normalize(self, row: dict[str, object]) -> dict[str, str]:
        return {
            field: "" if row.get(field) is None else str(row.get(field, ""))
            for field in self.fieldnames
        }

    def _write_file(self, path: Path, rows: Iterable[dict[str, object]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=self.fieldnames,
                quoting=csv.QUOTE_ALL,
                extrasaction="ignore",
            )
            writer.writeheader()
            for row in rows:
                writer.writerow(self._normalize(row))
