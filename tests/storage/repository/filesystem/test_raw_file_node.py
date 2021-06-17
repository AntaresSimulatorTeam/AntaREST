from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.raw_file_node import RawFileNode


def test_get(tmp_path: Path) -> None:
    file = tmp_path / "raw.txt"
    file.write_text("Hello")

    node = RawFileNode(context=Mock(), config=StudyConfig(file))
    assert node.get() == "Hello"


def test_validate(tmp_path: Path) -> None:
    file = tmp_path / "raw.txt"
    file.touch()

    node = RawFileNode(context=Mock(), config=StudyConfig(study_path=file))
    assert not node.check_errors("")

    node = RawFileNode(
        context=Mock(), config=StudyConfig(study_path=tmp_path / "fantom.txt")
    )
    assert "not exist" in node.check_errors("")[0]


def test_save(tmp_path: Path) -> None:
    file = tmp_path / "raw.txt"
    file.touch()

    node = RawFileNode(context=Mock(), config=StudyConfig(study_path=file))
    node.save("Hello")
    assert file.read_text() == "Hello"
