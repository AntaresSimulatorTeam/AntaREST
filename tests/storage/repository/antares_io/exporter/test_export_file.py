import json
from pathlib import Path
from zipfile import ZipFile

import pytest
from dirhash import dirhash

from antarest.storage.repository.antares_io.exporter.export_file import (
    Exporter,
)


@pytest.mark.unit_test
@pytest.mark.parametrize("outputs", [True, False])
def test_export_file(tmp_path: Path, outputs: bool):
    root = tmp_path / "folder"
    root.mkdir()
    (root / "test").mkdir()
    (root / "test/file.txt").write_text("Bonjour")
    (root / "file.txt").write_text("Hello, World")
    (root / "output").mkdir()
    (root / "output/file.txt").write_text("42")

    data = Exporter().export_file(root, outputs)
    zipf = ZipFile(data)

    assert "file.txt" in zipf.namelist()
    assert "test/" in zipf.namelist()
    assert "test/file.txt" in zipf.namelist()
    assert ("output/" in zipf.namelist()) == outputs
    assert ("output/file.txt" in zipf.namelist()) == outputs


@pytest.mark.unit_test
def test_export_flat(tmp_path: Path):
    root = tmp_path / "folder-with-output"
    root.mkdir()
    (root / "test").mkdir()
    (root / "test/file.txt").write_text("Bonjour")
    (root / "file.txt").write_text("Hello, World")
    (root / "output").mkdir()
    (root / "output/file.txt").write_text("42")

    root_without_output = tmp_path / "folder-without-output"
    root_without_output.mkdir()
    (root_without_output / "test").mkdir()
    (root_without_output / "test/file.txt").write_text("Bonjour")
    (root_without_output / "file.txt").write_text("Hello, World")

    root_hash = dirhash(root, "md5")
    root_without_output_hash = dirhash(root_without_output, "md5")
    Exporter().export_flat(root, tmp_path / "copy_with_output", outputs=True)

    copy_with_output_hash = dirhash(tmp_path / "copy_with_output", "md5")

    assert root_hash == copy_with_output_hash

    Exporter().export_flat(
        root, tmp_path / "copy_without_output", outputs=False
    )

    copy_without_output_hash = dirhash(tmp_path / "copy_without_output", "md5")

    assert root_without_output_hash == copy_without_output_hash


@pytest.mark.unit_test
def test_export_compact(tmp_path: Path):
    root = tmp_path / "folder"
    root.mkdir()
    (root / "input").mkdir()
    (root / "input/file.txt").write_text("Bonjour")
    (root / "output").mkdir()
    (root / "output/file.txt").write_text("Hello, World")

    data = {
        "input": {"file": "file/folder/input/file.txt"},
        "output": {"file": "file/folder/output/file.txt"},
    }

    buffer = Exporter().export_compact(root, data)
    zipf = ZipFile(buffer)

    zipf.extract("data.json", str(tmp_path.absolute()))
    data_res_path = tmp_path / "data.json"
    data_res = json.loads(data_res_path.read_text())

    assert f"res/{data_res['input']['file']}" in zipf.namelist()
    assert f"res/{data_res['output']['file']}" in zipf.namelist()
