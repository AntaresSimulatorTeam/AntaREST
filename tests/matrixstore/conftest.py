# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import unittest.mock

import pytest

from antarest.core.config import InternalMatrixFormat
from antarest.matrixstore.repository import MatrixContentRepository, MatrixDataSetRepository, MatrixRepository
from antarest.matrixstore.service import MatrixService

DEFAULT_INTERNAL_FORMAT = InternalMatrixFormat.TSV


@pytest.fixture(name="matrix_repo")
def matrix_repo_fixture() -> MatrixRepository:
    return MatrixRepository()


@pytest.fixture(name="dataset_repo")
def dataset_repo_fixture() -> MatrixDataSetRepository:
    return MatrixDataSetRepository()


@pytest.fixture(name="content_repo")
def content_repo_fixture(tmp_path) -> MatrixContentRepository:
    return MatrixContentRepository(tmp_path.joinpath("content_repo"), format=DEFAULT_INTERNAL_FORMAT)


@pytest.fixture(name="matrix_service")
def matrix_service_fixture(matrix_repo, dataset_repo, content_repo) -> MatrixService:
    return MatrixService(
        repo=matrix_repo,
        repo_dataset=dataset_repo,
        matrix_content_repository=content_repo,
        file_transfer_manager=unittest.mock.Mock(),
        task_service=unittest.mock.Mock(),
        config=unittest.mock.Mock(),
        user_service=unittest.mock.Mock(),
    )
