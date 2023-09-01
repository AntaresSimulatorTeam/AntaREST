from pathlib import Path
from unittest.mock import Mock

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
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
        path=file,
        study_id="id",
        version=-1,
        areas={
            "fr": Area(
                name="FR",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
            "de": Area(
                name="DE",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
            "it": Area(
                name="IT",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
        },
    )
    node = InputAreasList(context=Mock(), config=config)

    assert ["FR", "DE", "IT"] == node.get()
    assert not node.check_errors(["FR", "DE", "IT"])

    node.save(["a", "b", "c"])
    assert ["a", "b", "c"] == node.get()
