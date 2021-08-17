import zipfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)


@pytest.fixture
def empty_study(tmp_path: str) -> FileStudy:
    project_dir: Path = Path(__file__).parent.parent.parent.parent.parent
    empty_study_path: Path = project_dir / "resources" / "empty-study.zip"
    empty_study_destination_path = Path(tmp_path) / "empty-study"
    with zipfile.ZipFile(empty_study_path, "r") as zip_empty_study:
        zip_empty_study.extractall(empty_study_destination_path)

    config = FileStudyTreeConfig(
        study_path=empty_study_path,
        study_id="",
        version=-1,
        areas={},
        sets={},
    )
    file_study = FileStudy(
        config=config, tree=FileStudyTree(context=Mock(), config=config)
    )
    return file_study
