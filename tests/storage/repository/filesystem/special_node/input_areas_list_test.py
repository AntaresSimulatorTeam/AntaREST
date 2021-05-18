from pathlib import Path

from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.root.input.areas.list import (
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

    config = StudyConfig(
        study_path=file, areas={"fr": None, "de": None, "it": None}
    )
    node = InputAreasList(config=config)

    assert ["fr", "de", "it"] == node.get()
    assert not node.check_errors(["fr", "de", "it"])

    node.save(["a", "b", "c"])
    assert ["a", "b", "c"] == node.get()
