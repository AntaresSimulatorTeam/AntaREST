from pathlib import Path
from unittest.mock import Mock

from antarest.storage.repository.filesystem.bucket_node import BucketNode
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer


def build_bucket(tmp: Path) -> Path:
    bucket = tmp / "user"
    bucket.mkdir()
    (bucket / "fileA.txt").write_text("Content A")
    (bucket / "fileB.txt").touch()
    (bucket / "folder").mkdir()
    (bucket / "folder/fileC.txt").touch()

    return bucket


def test_get_bucket(tmp_path: Path):
    file = build_bucket(tmp_path)

    resolver = Mock()
    resolver.build_studyfile_uri.side_effect = [
        "fileA.txt",
        "fileB.txt",
        "fileC.txt",
    ]

    context = ContextServer(resolver=resolver, matrix=Mock())

    node = BucketNode(
        config=StudyConfig(study_path=file, study_id="id"), context=context
    )

    assert node.get(["fileA.txt"]) == b"Content A"
    bucket = node.get()
    assert "fileA.txt" in bucket["fileA.txt"]
    assert "fileB.txt" in bucket["fileB.txt"]
    assert "fileC.txt" in bucket["folder"]["fileC.txt"]


def test_save_bucket(tmp_path: Path):
    file = build_bucket(tmp_path)

    node = BucketNode(
        config=StudyConfig(study_path=file, study_id="id"), context=Mock()
    )
    node.save(data={"fileA.txt": b"Hello, World"})

    assert (file / "fileA.txt").read_text() == "Hello, World"
