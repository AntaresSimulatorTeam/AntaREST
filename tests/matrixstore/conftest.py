import unittest.mock

import pytest

from antarest.matrixstore.repository import (
    MatrixContentRepository,
    MatrixDataSetRepository,
    MatrixRepository,
)
from antarest.matrixstore.service import MatrixService


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
def matrix_service_fixture(
    matrix_repo, dataset_repo, content_repo
) -> MatrixService:
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
