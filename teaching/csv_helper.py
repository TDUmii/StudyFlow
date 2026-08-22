"""Các hàm CSV nhỏ, viết rõ từng bước để học sinh dễ đọc."""

import csv
import os
from pathlib import Path


def ensure_csv(file_path, fieldnames):
    """Tạo thư mục và file CSV có header nếu file chưa tồn tại."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists() or file_path.stat().st_size == 0:
        write_csv(file_path, fieldnames, [])


def read_csv(file_path, fieldnames):
    """Đọc CSV và trả về list chứa các dictionary."""
    ensure_csv(file_path, fieldnames)
    with Path(file_path).open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = []
        for row in reader:
            clean_row = {}
            for field in fieldnames:
                clean_row[field] = row.get(field, "") or ""
            rows.append(clean_row)
        return rows


def write_csv(file_path, fieldnames, rows):
    """Ghi an toàn: ghi file tạm trước, sau đó thay file cũ."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = file_path.with_suffix(".tmp")

    with temp_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    os.replace(temp_path, file_path)


def next_id(rows):
    """Tìm ID lớn nhất rồi cộng 1."""
    ids = []
    for row in rows:
        try:
            ids.append(int(row["id"]))
        except (KeyError, ValueError):
            pass
    return max(ids, default=0) + 1
