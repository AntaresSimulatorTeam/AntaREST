from pathlib import Path
from unittest.mock import Mock

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    Area,
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
                name="fr",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
            "de": Area(
                name="de",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
            "it": Area(
                name="it",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
        },
    )
    node = InputAreasList(context=Mock(), config=config)

    assert ["fr", "de", "it"] == node.get()
    assert not node.check_errors(["fr", "de", "it"])

    node.save(["a", "b", "c"])
    assert ["a", "b", "c"] == node.get()
