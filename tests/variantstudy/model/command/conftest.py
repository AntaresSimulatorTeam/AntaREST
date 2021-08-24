import zipfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.matrixstore.repository import (
    MatrixRepository,
    MatrixContentRepository,
    MatrixDataSetRepository,
)
from antarest.matrixstore.service import MatrixService
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
        study_path=empty_study_destination_path,
        path=empty_study_destination_path,
        study_id="",
        version=700,
        areas={},
        sets={},
    )
    file_study = FileStudy(
        config=config, tree=FileStudyTree(context=Mock(), config=config)
    )
    return file_study


@pytest.fixture
def matrix_service() -> MatrixService:
    repo = Mock()
    content = Mock()
    content.save.return_value = "matrix_id"
    dataset_repo = Mock()

    service = MatrixService(
        repo=repo,
        repo_dataset=dataset_repo,
        content=content,
        user_service=Mock(),
    )
    return service
