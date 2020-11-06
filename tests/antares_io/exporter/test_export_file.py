import base64
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from api_iso_antares.antares_io.exporter.export_file import Exporter


def test_export_file(tmp_path: Path):
    root = tmp_path / "folder"
    root.mkdir()
    (root / "test").mkdir()
    (root / "test/file.txt").write_text("Bonjour")
    (root / "file.txt").write_text("Hello, World")

    data = Exporter().export_file(root)
    zipf = ZipFile(data)

    assert "folder/file.txt" in zipf.namelist()
    assert "folder/test/" in zipf.namelist()
    assert "folder/test/file.txt" in zipf.namelist()
