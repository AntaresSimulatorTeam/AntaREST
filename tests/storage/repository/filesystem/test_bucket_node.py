from pathlib import Path

from antarest.storage.repository.filesystem.bucket_node import BucketNode
from antarest.storage.repository.filesystem.config.model import StudyConfig


def build_bucket(tmp: Path) -> Path:
    bucket = tmp / "user"
    bucket.mkdir()
    (bucket / "fileA.txt").touch()
    (bucket / "fileB.txt").touch()
    (bucket / "folder").mkdir()
    (bucket / "folder/fileC.txt").touch()

    return bucket


def test_get_bucket(tmp_path: Path):
    bucket = build_bucket(tmp_path)

    expected = {
        "fileA.txt": "file/user/fileA.txt",
        "fileB.txt": "file/user/fileB.txt",
        "folder/fileC.txt": "file/user/folder/fileC.txt",
    }

    node = BucketNode(config=StudyConfig(study_path=bucket))

    assert node.get(["fileA.txt"]) == "file/user/fileA.txt"
    assert node.get() == expected


def test_save_bucket(tmp_path: Path):
    bucket = build_bucket(tmp_path)

    (tmp_path / "new.txt").write_text("Hello, World")

    node = BucketNode(config=StudyConfig(study_path=bucket))
    node.save(data="file/new.txt", url=["fileA.txt"])

    assert (bucket / "fileA.txt").read_text() == "Hello, World"
