from pathlib import Path
from unittest.mock import Mock

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


def test_get(tmp_path: Path) -> None:
    file = tmp_path / "input.txt"
    content = """
100000	100000	0.010000	0.010000	0	0	0	0
100000	100000	0.010000	0.010000	0	0	0	0
    """
    file.write_text(content)

    config = FileStudyTreeConfig(study_path=file, version=-1, study_id="id")
    node = InputSeriesMatrix(context=Mock(), config=config, nb_columns=8)

    assert node.load() == {
        "columns": [0, 1, 2, 3, 4, 5, 6, 7],
        "data": [
            [100000.0, 100000.0, 0.01, 0.01, 0.0, 0.0, 0.0, 0.0],
            [100000.0, 100000.0, 0.01, 0.01, 0.0, 0.0, 0.0, 0.0],
        ],
        "index": [0, 1],
    }


def test_save(tmp_path: Path) -> None:
    file = tmp_path / "input.txt"
    file.write_text("\n")

    config = FileStudyTreeConfig(study_path=file, study_id="id", version=-1)
    node = InputSeriesMatrix(context=Mock(), config=config)

    node.dump({"columns": [0, 1], "data": [[1, 2], [3, 4]], "index": [0, 1]})
    assert (
        file.read_text()
        == """1\t2
3\t4
"""
    )
