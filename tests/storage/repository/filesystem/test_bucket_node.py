from pathlib import Path
from unittest.mock import Mock

from antarest.study.storage.rawstudy.model.filesystem.bucket_node import (
    BucketNode,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)


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
        config=FileStudyTreeConfig(study_path=file, study_id="id", version=-1),
        context=context,
    )

    assert node.get(["fileA.txt"]) == b"Content A"
    bucket = node.get()
    assert "fileA.txt" in bucket["fileA.txt"]
    assert "fileB.txt" in bucket["fileB.txt"]
    assert "fileC.txt" in bucket["folder"]["fileC.txt"]


def test_save_bucket(tmp_path: Path):
    file = build_bucket(tmp_path)

    node = BucketNode(
        config=FileStudyTreeConfig(study_path=file, study_id="id", version=-1),
        context=Mock(),
    )
    node.save(data={"fileA.txt": b"Hello, World"})

    assert (file / "fileA.txt").read_text() == "Hello, World"
