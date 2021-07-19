from pathlib import Path
from unittest.mock import Mock

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.areas.list import (
    InputAreasList,
)


def test(tmp_path: Path):
    file = tmp_path / "list.txt"
    content = """
FR
DE
IT    
"""
    file.write_text(content)

    config = FileStudyTreeConfig(
        study_path=file,
        study_id="id",
        areas={"fr": None, "de": None, "it": None},
    )
    node = InputAreasList(context=Mock(), config=config)

    assert ["fr", "de", "it"] == node.get()
    assert not node.check_errors(["fr", "de", "it"])

    node.save(["a", "b", "c"])
    assert ["a", "b", "c"] == node.get()
