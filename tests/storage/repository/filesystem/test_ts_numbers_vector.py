from pathlib import Path
from unittest.mock import Mock

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.ts_numbers.ts_numbers_data import (
    TsNumbersVector,
)


def test_get(tmp_path: Path) -> None:
    file = tmp_path / "raw.txt"
    file.write_text("size:1x5\n4\n5\n100\n8\n1")

    node = TsNumbersVector(
        context=Mock(),
        config=FileStudyTreeConfig(
            study_path=file, path=file, version=-1, study_id="id"
        ),
    )
    assert node.get() == [4, 5, 100, 8, 1]


def test_save(tmp_path: Path) -> None:
    file = tmp_path / "raw.txt"
    file.touch()

    node = TsNumbersVector(
        context=Mock(),
        config=FileStudyTreeConfig(
            study_path=file, path=file, version=-1, study_id="id"
        ),
    )
    node.save([4, 5, 100, 8, 2, 10])
    assert file.read_text() == "size:1x6\n4\n5\n100\n8\n2\n10"


def test_coverage() -> None:
    node = TsNumbersVector(
        context=Mock(),
        config=Mock(),
    )
    node.normalize()
    node.denormalize()
    assert node.check_errors(Mock()) == []
