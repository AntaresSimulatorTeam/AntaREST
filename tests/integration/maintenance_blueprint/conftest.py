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
from conftest_db import db_engine_fixture, db_middleware_fixture
from matrixstore.conftest import (
    content_repo_fixture,
    dataset_repo_fixture,
    matrix_repo_fixture,
    matrix_service_fixture,
)

from antarest.blobstore.repository import BlobContentRepository
from antarest.blobstore.service import BlobService
from antarest.core.config import Config
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.tasks.repository import TaskJobRepository
from antarest.core.tasks.service import ITaskService, TaskJobService
from antarest.eventbus.business.local_eventbus import LocalEventBus
from antarest.eventbus.service import EventBusService

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


@pytest.fixture(name="event_bus", scope="session")
def event_bus_fixture() -> IEventBus:
    """
    Fixture that creates a Mock instance of IEventBus with a session-level scope.

    Returns:
        A Mock instance of the IEventBus class for event bus-related testing.
    """
    return EventBusService(LocalEventBus())


@pytest.fixture
def task_service(task_job_repository: TaskJobRepository, event_bus: IEventBus) -> ITaskService:
    config = Config()
    return TaskJobService(config=config, repository=task_job_repository, event_bus=event_bus)


@pytest.fixture
def task_job_repository() -> TaskJobRepository:
    return TaskJobRepository()
