import datetime
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

import pytest

from antarest.core.config import (
    Config,
    SecurityConfig,
    StorageConfig,
    WorkspaceConfig,
)
from antarest.storage.business.rawstudy.exporter_service import ExporterService
from antarest.storage.business.rawstudy.importer_service import ImporterService
from antarest.storage.business.rawstudy.raw_study_service import (
    RawStudyService,
)
from antarest.storage.main import build_storage
from antarest.storage.model import Study, DEFAULT_WORKSPACE_NAME, RawStudy
from antarest.storage.repository.filesystem.factory import StudyFactory
from antarest.storage.service import StudyService


@pytest.fixture
def sta_mini_path(tmp_path: str) -> Path:
    return Path(tmp_path) / "studies" / "STA-mini"


@pytest.fixture
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


@pytest.fixture
def storage_service(
    tmp_path: str, project_path: Path, sta_mini_zip_path: Path
) -> StudyService:

    path_studies = Path(tmp_path) / "studies"

    path_resources = project_path / "resources"

    with ZipFile(sta_mini_zip_path) as zip_output:
        zip_output.extractall(path=path_studies)

    md = RawStudy(
        id="STA-mini",
        name="STA-mini",
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(path_studies / "STA-mini"),
        created_at=datetime.datetime.fromtimestamp(1480683452),
        updated_at=datetime.datetime.fromtimestamp(1602678639),
        version=700,
    )
    repo = Mock()
    repo.get.side_effect = lambda name: RawStudy(
        id=name,
        name=name,
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(path_studies / name),
        created_at=datetime.datetime.fromtimestamp(1480683452),
        updated_at=datetime.datetime.fromtimestamp(1602678639),
        version=700,
    )
    repo.get_all.return_value = [md]

    config = Config(
        resources_path=path_resources,
        security=SecurityConfig(disabled=True),
        storage=StorageConfig(
            workspaces={
                DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=path_studies)
            }
        ),
    )

    storage_service = build_storage(
        application=Mock(),
        user_service=Mock(),
        matrix_service=Mock(),
        config=config,
        metadata_repository=repo,
    )

    return storage_service
