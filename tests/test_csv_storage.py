import csv

from app.storage.csv_storage import CSVStorage


def test_create_append_read_update_delete_and_header(tmp_path):
    path = tmp_path / "items.csv"
    storage = CSVStorage(path, ["id", "content"])
    assert path.exists()
    assert path.read_text(encoding="utf-8-sig").strip().startswith('"id","content"')
    content = 'Tiếng Việt, includes "quotes"\nand a new line'
    storage.append({"id": 1, "content": content})
    assert storage.read_all() == [{"id": "1", "content": content}]
    assert storage.update(1, {"content": "changed"})
    assert storage.read_all()[0]["content"] == "changed"
    assert storage.delete(1)
    assert storage.read_all() == []


def test_missing_empty_and_malformed_file_are_safe(tmp_path):
    path = tmp_path / "data.csv"
    storage = CSVStorage(path, ["id", "name"])
    path.unlink()
    assert storage.read_all() == [] and path.exists()
    path.write_text('"id","name"\n"1","Good"\n"2","Bad","extra"\n', encoding="utf-8")
    assert storage.read_all() == [{"id": "1", "name": "Good"}]


def test_atomic_rewrite_leaves_no_temp_file(tmp_path):
    storage = CSVStorage(tmp_path / "safe.csv", ["id"])
    storage.write_all([{"id": "4"}])
    assert storage.read_all() == [{"id": "4"}]
    assert not (tmp_path / "safe.csv.tmp").exists()
