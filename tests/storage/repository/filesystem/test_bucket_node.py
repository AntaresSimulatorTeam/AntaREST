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
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)


def build_bucket(tmp: Path) -> Path:
    bucket = tmp / "user"
    bucket.mkdir()
    (bucket / "fileA.txt").write_text("Content A")
    (bucket / "fileB.txt").touch()
    (bucket / "folder").mkdir()
    (bucket / "folder/fileC.txt").touch()
    (bucket / "registered_file.ini").touch()
    (bucket / "registered_folder_node").mkdir()

    return bucket


def test_get_bucket(tmp_path: Path):
    registered_files = {
        "registered_file.ini": IniFileNode,
        # "registered_folder_node": FolderNode,
    }

    file = build_bucket(tmp_path)

    resolver = Mock()
    resolver.build_studyfile_uri.side_effect = [
        "fileA.txt",
        "fileB.txt",
        "fileC.txt",
    ]

    context = ContextServer(resolver=resolver, matrix=Mock())

    node = BucketNode(
        config=FileStudyTreeConfig(
            study_path=file, path=file, study_id="id", version=-1
        ),
        context=context,
        registered_files=registered_files,
    )

    assert node.get(["fileA.txt"]) == b"Content A"
    bucket = node.get()
    assert "fileA.txt" in bucket["fileA.txt"]
    assert "fileB.txt" in bucket["fileB.txt"]
    assert "fileC.txt" in bucket["folder"]["fileC.txt"]
    for file_name, node_type in registered_files.items():
        assert (
            type(node._get([file_name.split(".")[0]], get_node=True))
            == node_type
        )


def test_save_bucket(tmp_path: Path):
    file = build_bucket(tmp_path)

    node = BucketNode(
        config=FileStudyTreeConfig(
            study_path=file, path=file, study_id="id", version=-1
        ),
        context=Mock(),
    )
    node.save(data={"fileA.txt": b"Hello, World"})

    assert (file / "fileA.txt").read_text() == "Hello, World"

    node.save(data={"fileC.txt": b"test"}, url=["folder"])
    assert (file / "folder" / "fileC.txt").read_text() == "test"

    node.save(data=b"test2", url=["folder", "fileC.txt"])
    assert (file / "folder" / "fileC.txt").read_text() == "test2"
