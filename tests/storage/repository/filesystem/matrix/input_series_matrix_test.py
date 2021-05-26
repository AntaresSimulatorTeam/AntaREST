from pathlib import Path

from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


def test_get(tmp_path: Path) -> None:
    file = tmp_path / "input.txt"
    content = """
100000	100000	0.010000	0.010000	0	0	0	0
100000	100000	0.010000	0.010000	0	0	0	0
    """
    file.write_text(content)

    config = StudyConfig(study_path=file)
    node = InputSeriesMatrix(config, nb_columns=8)

    assert "file://" in node.get(expanded=True)

    assert node.get() == {
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

    config = StudyConfig(study_path=file)
    node = InputSeriesMatrix(config)

    node.save({"columns": [0, 1], "data": [[1, 2], [3, 4]], "index": [0, 1]})
    assert (
        file.read_text()
        == """1\t2
3\t4
"""
    )
