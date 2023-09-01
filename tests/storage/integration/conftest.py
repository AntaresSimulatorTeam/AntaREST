import datetime
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

import pytest
from sqlalchemy import create_engine

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.config import CacheConfig, Config, SecurityConfig, StorageConfig, WorkspaceConfig
from antarest.core.tasks.service import ITaskService
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.dbmodel import Base
from antarest.login.model import User
from antarest.matrixstore.service import SimpleMatrixService
from antarest.study.main import build_study_service
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy, StudyAdditionalData
from antarest.study.service import StudyService


@pytest.fixture
def sta_mini_path(tmp_path: Path) -> Path:
    return tmp_path / "studies" / "STA-mini"


@pytest.fixture
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


@pytest.fixture
def storage_service(
    tmp_path: Path, project_path: Path, sta_mini_zip_path: Path
) -> StudyService:
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    # noinspection SpellCheckingInspection
    DBSessionMiddleware(
        None,
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )
    path_studies = tmp_path / "studies"

    path_resources = project_path / "resources"

    with ZipFile(sta_mini_zip_path) as zip_output:
        zip_output.extractall(path=path_studies)

    # noinspection PyArgumentList
    md = RawStudy(
        id="STA-mini",
        name="STA-mini",
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(path_studies / "STA-mini"),
        created_at=datetime.datetime.fromtimestamp(1480683452),
        updated_at=datetime.datetime.fromtimestamp(1602678639),
        version=700,
        additional_data=StudyAdditionalData(
            author="Andrea SGATTONI", horizon=2030
        ),
    )
    repo = Mock()
    # noinspection PyArgumentList
    repo.get.side_effect = lambda name: RawStudy(
        id=name,
        name=name,
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(path_studies / name),
        created_at=datetime.datetime.fromtimestamp(1480683452),
        updated_at=datetime.datetime.fromtimestamp(1602678639),
        version=700,
        additional_data=StudyAdditionalData(),
    )
    repo.get_all.return_value = [md]

    variant_repo = Mock()
    variant_repo.get_children.return_value = []

    config = Config(
        resources_path=path_resources,
        security=SecurityConfig(disabled=True),
        cache=CacheConfig(),
        storage=StorageConfig(
            workspaces={
                DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=path_studies)
            }
        ),
    )

    task_service_mock = Mock(spec=ITaskService)
    user_service = Mock()
    # noinspection PyArgumentList
    user_service.get_user.return_value = User(id=0, name="test")

    matrix_path = tmp_path / "matrices"
    matrix_path.mkdir()
    matrix_service = SimpleMatrixService(matrix_path)
    storage_service = build_study_service(
        application=Mock(),
        cache=LocalCache(config=config.cache),
        file_transfer_manager=Mock(),
        task_service=task_service_mock,
        user_service=user_service,
        matrix_service=matrix_service,
        config=config,
        metadata_repository=repo,
        variant_repository=variant_repo,
    )

    return storage_service
