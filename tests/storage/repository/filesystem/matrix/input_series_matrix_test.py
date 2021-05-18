from pathlib import Path

from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


def test(tmp_path: Path) -> None:
    file = tmp_path / "input.txt"
    content = """
100000	100000	0.010000	0.010000	0	0	0	0
100000	100000	0.010000	0.010000	0	0	0	0
    """
    file.write_text(content)

    config = StudyConfig(study_path=file)
    node = InputSeriesMatrix(config, nb_columns=8)
    assert node.get() == {
        0: {0: 100000.0, 1: 100000.0},
        1: {0: 100000.0, 1: 100000.0},
        2: {0: 0.01, 1: 0.01},
        3: {0: 0.01, 1: 0.01},
        4: {0: 0.0, 1: 0.0},
        5: {0: 0.0, 1: 0.0},
        6: {0: 0.0, 1: 0.0},
        7: {0: 0.0, 1: 0.0},
    }
    node.save({i: {0: i} for i in range(0, 8)})
    assert node.get() == {
        0: {0: 0.0},
        1: {0: 1.0},
        2: {0: 2.0},
        3: {0: 3.0},
        4: {0: 4.0},
        5: {0: 5.0},
        6: {0: 6.0},
        7: {0: 7.0},
    }

    assert not node.check_errors({i: {0: i} for i in range(0, 8)})
