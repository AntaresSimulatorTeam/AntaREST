# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

"""Fixtures for maintenance integration tests."""

from pathlib import Path

import pytest

from antarest.blobstore.repository import BlobContentRepository
from antarest.blobstore.service import BlobService
from tests.conftest_db import db_engine_fixture, db_middleware_fixture
from tests.matrixstore.conftest import (
    content_repo_fixture,
    dataset_repo_fixture,
    matrix_repo_fixture,
    matrix_service_fixture,
)

db_engine = db_engine_fixture
db_middleware = db_middleware_fixture
matrix_repo = matrix_repo_fixture
dataset_repo = dataset_repo_fixture
content_repo = content_repo_fixture
matrix_service = matrix_service_fixture


@pytest.fixture(name="simple_blob_service")
def simple_blob_service_fixture(tmp_path: Path) -> BlobService:
    """
    Function-scoped BlobService fixture for isolation between tests.

    Each test gets a fresh BlobService with an empty blob store.
    """
    blob_dir = tmp_path / "blob_store"
    blob_dir.mkdir()
    blob_content_repository = BlobContentRepository(bucket_dir=blob_dir)
    return BlobService(blob_content_repository=blob_content_repository)
