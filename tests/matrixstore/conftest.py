import unittest.mock

import pytest
from sqlalchemy import create_engine

from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.dbmodel import Base
from antarest.matrixstore.repository import MatrixContentRepository, MatrixDataSetRepository, MatrixRepository
from antarest.matrixstore.service import MatrixService


@pytest.fixture(name="db_engine")
def db_engine_fixture():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(name="db_middleware", autouse=True)
def db_middleware_fixture(db_engine):
    yield DBSessionMiddleware(
        None,
        custom_engine=db_engine,
        session_args={"autocommit": False, "autoflush": False},
    )


@pytest.fixture(name="matrix_repo")
def matrix_repo_fixture() -> MatrixRepository:
    yield MatrixRepository()


@pytest.fixture(name="dataset_repo")
def dataset_repo_fixture() -> MatrixDataSetRepository:
    yield MatrixDataSetRepository()


@pytest.fixture(name="content_repo")
def content_repo_fixture(tmp_path) -> MatrixContentRepository:
    yield MatrixContentRepository(tmp_path.joinpath("content_repo"))


@pytest.fixture(name="matrix_service")
def matrix_service_fixture(matrix_repo, dataset_repo, content_repo) -> MatrixService:
    yield MatrixService(
        repo=matrix_repo,
        repo_dataset=dataset_repo,
        matrix_content_repository=content_repo,
        file_transfer_manager=unittest.mock.Mock(),
        task_service=unittest.mock.Mock(),
        config=unittest.mock.Mock(),
        user_service=unittest.mock.Mock(),
    )


@pytest.fixture(name="matrix_content_repo")
def matrix_content_repo_fixture(tmp_path) -> MatrixContentRepository:
    yield MatrixContentRepository(bucket_dir=tmp_path.joinpath("matrix-store"))
