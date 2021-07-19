from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.raw_file_node import RawFileNode


def test_get(tmp_path: Path) -> None:
    file = tmp_path / "raw.txt"
    file.write_text("Hello")

    node = RawFileNode(
        context=Mock(), config=FileStudyTreeConfig(file, study_id="id")
    )
    assert node.get() == b"Hello"


def test_validate(tmp_path: Path) -> None:
    file = tmp_path / "raw.txt"
    file.touch()

    node = RawFileNode(
        context=Mock(),
        config=FileStudyTreeConfig(study_path=file, study_id="id"),
    )
    assert not node.check_errors("")

    node = RawFileNode(
        context=Mock(),
        config=FileStudyTreeConfig(
            study_path=tmp_path / "fantom.txt", study_id="id"
        ),
    )
    assert "not exist" in node.check_errors("")[0]


def test_save(tmp_path: Path) -> None:
    file = tmp_path / "raw.txt"
    file.touch()

    node = RawFileNode(
        context=Mock(),
        config=FileStudyTreeConfig(study_path=file, study_id="id"),
    )
    node.save(b"Hello")
    assert file.read_text() == "Hello"
