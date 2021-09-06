from pathlib import Path
from unittest.mock import Mock

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import (
    RawFileNode,
)


def test_get(tmp_path: Path) -> None:
    file = tmp_path / "raw.txt"
    file.write_text("Hello")

    node = RawFileNode(
        context=Mock(),
        config=FileStudyTreeConfig(
            study_path=file, path=file, version=-1, study_id="id"
        ),
    )
    assert node.get() == b"Hello"


def test_validate(tmp_path: Path) -> None:
    file = tmp_path / "raw.txt"
    file.touch()

    node = RawFileNode(
        context=Mock(),
        config=FileStudyTreeConfig(
            study_path=file, path=file, version=-1, study_id="id"
        ),
    )
    assert not node.check_errors("")

    new_path = tmp_path / "fantom.txt"
    node = RawFileNode(
        context=Mock(),
        config=FileStudyTreeConfig(
            study_path=new_path, path=new_path, version=-1, study_id="id"
        ),
    )
    assert "not exist" in node.check_errors("")[0]


def test_save(tmp_path: Path) -> None:
    file = tmp_path / "raw.txt"
    file.touch()

    node = RawFileNode(
        context=Mock(),
        config=FileStudyTreeConfig(
            study_path=file, path=file, version=-1, study_id="id"
        ),
    )
    node.save(b"Hello")
    assert file.read_text() == "Hello"
