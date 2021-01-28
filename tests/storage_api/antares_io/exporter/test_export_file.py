import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from antarest.storage_api.antares_io.exporter.export_file import Exporter


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
