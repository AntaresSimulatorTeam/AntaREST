from pathlib import Path

from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.root.user.user import User


def build_bucket(tmp: Path) -> Path:
    bucket = tmp / "user"
    bucket.mkdir()
    (bucket / "fileA.txt").touch()
    (bucket / "fileB.txt").touch()
    (bucket / "folder").mkdir()
    (bucket / "folder/fileC.txt").touch()

    return bucket


def test_bucket(tmp_path: Path):
    bucket = build_bucket(tmp_path)

    expected = {
        "fileA.txt": "file/user/fileA.txt",
        "fileB.txt": "file/user/fileB.txt",
        "folder": "file/user/folder",
        "folder/fileC.txt": "file/user/folder/fileC.txt",
    }

    node = User(config=Config(study_path=bucket))

    assert node.get(["fileA.txt"]) == "file/user/fileA.txt"
    assert node.get() == expected
