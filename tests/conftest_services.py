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

"""
This module provides various pytest fixtures for unit testing the AntaREST application.

Fixtures in this module are used to set up and provide instances of different classes
and services required during testing.
"""

import datetime
import typing as t
import uuid
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.core.config import Config, InternalMatrixFormat, StorageConfig, WorkspaceConfig
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.tasks.model import CustomTaskEventMessages, TaskDTO, TaskListFilter, TaskResult, TaskStatus, TaskType
from antarest.core.tasks.service import ITaskService, NoopNotifier, Task
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.eventbus.business.local_eventbus import LocalEventBus
from antarest.eventbus.service import EventBusService
from antarest.matrixstore.repository import MatrixContentRepository
from antarest.matrixstore.service import MatrixService, SimpleMatrixService
from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.repository import VariantStudyRepository
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService

__all__ = (
    "command_context_fixture",
    "bucket_dir_fixture",
    "simple_matrix_service_fixture",
    "generator_matrix_constants_fixture",
    "uri_resolver_service_fixture",
    "core_cache_fixture",
    "study_factory_fixture",
    "core_config_fixture",
    "task_service_fixture",
    "event_bus_fixture",
    "command_factory_fixture",
    "variant_study_repository_fixture",
    "raw_study_service_fixture",
    "variant_study_service_fixture",
    "study_storage_service_fixture",
    "study_service_fixture",
)


class SynchTaskService(ITaskService):
    def __init__(self) -> None:
        self._task_result: t.Optional[TaskResult] = None

    def add_worker_task(
        self,
        task_type: TaskType,
        task_queue: str,
        task_args: t.Dict[str, t.Union[int, float, bool, str]],
        name: t.Optional[str],
        ref_id: t.Optional[str],
    ) -> t.Optional[str]:
        raise NotImplementedError()

    def add_task(
        self,
        action: Task,
        name: t.Optional[str],
        task_type: t.Optional[TaskType],
        ref_id: t.Optional[str],
        progress: t.Optional[int],
        custom_event_messages: t.Optional[CustomTaskEventMessages],
    ) -> str:
        self._task_result = action(NoopNotifier())
        return str(uuid.uuid4())

    def status_task(self, task_id: str, with_logs: bool = False) -> TaskDTO:
        return TaskDTO(
            id=task_id,
            name="mock",
            owner=None,
            status=TaskStatus.COMPLETED,
            creation_date_utc=datetime.datetime.now().isoformat(" "),
            completion_date_utc=None,
            result=self._task_result,
            logs=None,
        )

    def list_tasks(self, task_filter: TaskListFilter) -> t.List[TaskDTO]:
        return []

    def await_task(self, task_id: str, timeout_sec: t.Optional[int] = None) -> None:
        pass


@pytest.fixture(name="command_context")
def command_context_fixture(matrix_service: MatrixService) -> CommandContext:
    """
    Fixture for creating a CommandContext object.

    Args:
        matrix_service: The MatrixService object.

    Returns:
        CommandContext: The CommandContext object.
    """
    # sourcery skip: inline-immediately-returned-variable
    generator_matrix_constants = GeneratorMatrixConstants(matrix_service)
    generator_matrix_constants.init_constant_matrices()
    command_context = CommandContext(
        generator_matrix_constants=generator_matrix_constants,
        matrix_service=matrix_service,
    )
    return command_context


@pytest.fixture(name="bucket_dir", scope="session")
def bucket_dir_fixture(tmp_path_factory: t.Any) -> Path:
    """
    Fixture that creates a session-level temporary directory named "matrix_store" for storing matrices.

    This fixture is used with the "session" scope to share the same directory among all tests.
    This sharing optimizes test execution speed and reduces disk space usage in the temporary directory.
    It is safe to share the directory as matrices have unique identifiers.

    Args:
        tmp_path_factory: A fixture provided by pytest to generate temporary directories.

    Returns:
        A Path object representing the created temporary directory for storing matrices.
    """
    return t.cast(Path, tmp_path_factory.mktemp("matrix_store"))


@pytest.fixture(name="simple_matrix_service", scope="session")
def simple_matrix_service_fixture(bucket_dir: Path) -> SimpleMatrixService:
    """
    Fixture that creates a SimpleMatrixService instance using the session-level temporary directory.

    Args:
        bucket_dir: The session-level temporary directory for storing matrices.

    Returns:
        An instance of the SimpleMatrixService class representing the matrix service.
    """
    matrix_content_repository = MatrixContentRepository(bucket_dir=bucket_dir, format=InternalMatrixFormat.TSV)
    return SimpleMatrixService(matrix_content_repository=matrix_content_repository)


@pytest.fixture(name="generator_matrix_constants", scope="session")
def generator_matrix_constants_fixture(
    simple_matrix_service: SimpleMatrixService,
) -> GeneratorMatrixConstants:
    """
    Fixture that creates a GeneratorMatrixConstants instance with a session-level scope.

    Args:
        simple_matrix_service: An instance of the SimpleMatrixService class.

    Returns:
        An instance of the GeneratorMatrixConstants class representing the matrix constants generator.
    """
    out_generator_matrix_constants = GeneratorMatrixConstants(simple_matrix_service)
    out_generator_matrix_constants.init_constant_matrices()
    return out_generator_matrix_constants


@pytest.fixture(name="uri_resolver_service", scope="session")
def uri_resolver_service_fixture(
    simple_matrix_service: SimpleMatrixService,
) -> UriResolverService:
    """
    Fixture that creates an UriResolverService instance with a session-level scope.

    Args:
        simple_matrix_service: An instance of the SimpleMatrixService class.

    Returns:
        An instance of the UriResolverService class representing the URI resolver service.
    """
    return UriResolverService(matrix_service=simple_matrix_service)


@pytest.fixture(name="core_cache", scope="session")
def core_cache_fixture() -> ICache:
    """
    Fixture that creates an ICache instance with a session-level scope.
    We use the Mock class to create a dummy cache object that doesn't store any data.

    Returns:
        An instance of the Mock class representing the cache object.
    """
    cache = Mock(spec=ICache)
    cache.get.return_value = None  # don't use cache
    return cache


@pytest.fixture(name="study_factory", scope="session")
def study_factory_fixture(
    simple_matrix_service: SimpleMatrixService,
    uri_resolver_service: UriResolverService,
    core_cache: ICache,
) -> StudyFactory:
    """
    Fixture that creates a StudyFactory instance with a session-level scope.

    Args:
        simple_matrix_service: An instance of the SimpleMatrixService class.
        uri_resolver_service: An instance of the UriResolverService class.
        core_cache: An instance of the ICache class.

    Returns:
        An instance of the StudyFactory class representing the study factory used for all tests.
    """
    return StudyFactory(
        matrix=simple_matrix_service,
        resolver=uri_resolver_service,
        cache=core_cache,
    )


@pytest.fixture(name="core_config")
def core_config_fixture(
    tmp_path: Path,
    project_path: Path,
    bucket_dir: Path,
) -> Config:
    """
    Fixture that creates a Config instance for the core application configuration.

    Args:
        tmp_path: A Path object representing the temporary directory provided by pytest.
        project_path: A Path object representing the project's directory.
        bucket_dir: A Path object representing the directory for storing matrices.

    Returns:
        An instance of the Config class with the provided configuration settings.
    """
    tmp_dir = tmp_path.joinpath("tmp")
    tmp_dir.mkdir(exist_ok=True)
    return Config(
        storage=StorageConfig(
            matrixstore=bucket_dir,
            archive_dir=tmp_path.joinpath("archives"),
            tmp_dir=tmp_dir,
            workspaces={
                "default": WorkspaceConfig(
                    path=tmp_path.joinpath("internal_studies"),
                ),
                "studies": WorkspaceConfig(
                    path=tmp_path.joinpath("studies"),
                ),
            },
        ),
        resources_path=project_path.joinpath("resources"),
        root_path=str(tmp_path),
    )


@pytest.fixture(name="task_service", scope="session")
def task_service_fixture() -> ITaskService:
    """
    Fixture that creates a Mock instance of ITaskService with a session-level scope.

    Returns:
        A Mock instance of the ITaskService class for task-related testing.
    """
    return SynchTaskService()


@pytest.fixture(name="event_bus", scope="session")
def event_bus_fixture() -> IEventBus:
    """
    Fixture that creates a Mock instance of IEventBus with a session-level scope.

    Returns:
        A Mock instance of the IEventBus class for event bus-related testing.
    """
    return EventBusService(LocalEventBus())


@pytest.fixture(name="command_factory", scope="session")
def command_factory_fixture(
    generator_matrix_constants: GeneratorMatrixConstants,
    simple_matrix_service: SimpleMatrixService,
) -> CommandFactory:
    """
    Fixture that creates a CommandFactory instance with a session-level scope.

    Args:
        generator_matrix_constants: An instance of the GeneratorMatrixConstants class.
        simple_matrix_service: An instance of the SimpleMatrixService class.

    Returns:
        An instance of the CommandFactory class with the provided dependencies.
    """
    return CommandFactory(
        generator_matrix_constants=generator_matrix_constants,
        matrix_service=simple_matrix_service,
    )


# noinspection PyUnusedLocal
@pytest.fixture(name="variant_study_repository")
def variant_study_repository_fixture(
    core_cache: ICache,
    db_middleware: DBSessionMiddleware,  # required
) -> VariantStudyRepository:
    """
    Fixture that creates a VariantStudyRepository instance.

    Args:
        core_cache: An instance of the ICache class.
        db_middleware: An instance of the DBSessionMiddleware class.

    Returns:
        An instance of the VariantStudyRepository class with the provided cache service.
    """
    return VariantStudyRepository(cache_service=core_cache)


@pytest.fixture(name="raw_study_service")
def raw_study_service_fixture(
    core_config: Config,
    study_factory: StudyFactory,
    core_cache: ICache,
) -> RawStudyService:
    """
    Fixture that creates a RawStudyService instance.

    Args:
        core_config: An instance of the Config class representing the core application configuration.
        study_factory: An instance of the StudyFactory class.
        core_cache: An instance of the ICache class.

    Returns:
        An instance of the RawStudyService class with the provided dependencies.
    """
    return RawStudyService(
        config=core_config,
        study_factory=study_factory,
        cache=core_cache,
    )


@pytest.fixture(name="variant_study_service")
def variant_study_service_fixture(
    task_service: ITaskService,
    core_cache: ICache,
    raw_study_service: RawStudyService,
    command_factory: CommandFactory,
    study_factory: StudyFactory,
    variant_study_repository: VariantStudyRepository,
    event_bus: IEventBus,
    core_config: Config,
) -> VariantStudyService:
    """
    Fixture that creates a VariantStudyService instance.

    Args:
        task_service: An instance of the ITaskService class.
        core_cache: An instance of the ICache class.
        raw_study_service: An instance of the RawStudyService class.
        command_factory: An instance of the CommandFactory class.
        study_factory: An instance of the StudyFactory class.
        variant_study_repository: An instance of the VariantStudyRepository class.
        event_bus: An instance of the IEventBus class.
        core_config: An instance of the Config class representing the core application configuration.

    Returns:
        An instance of the VariantStudyService class with the provided dependencies.
    """
    return VariantStudyService(
        task_service=task_service,
        cache=core_cache,
        raw_study_service=raw_study_service,
        command_factory=command_factory,
        study_factory=study_factory,
        repository=variant_study_repository,
        event_bus=event_bus,
        config=core_config,
    )


@pytest.fixture(name="study_storage_service")
def study_storage_service_fixture(
    raw_study_service: RawStudyService,
    variant_study_service: VariantStudyService,
) -> StudyStorageService:
    """
    Fixture that creates a StudyStorageService instance for study storage-related testing.

    Args:
        raw_study_service: The RawStudyService instance.
        variant_study_service: The VariantStudyService instance.

    Returns:
        An instance of the StudyStorageService class representing the study storage service.
    """
    return StudyStorageService(
        raw_study_service=raw_study_service,
        variant_study_service=variant_study_service,
    )


@pytest.fixture(name="study_service")
def study_service_fixture(
    raw_study_service: RawStudyService,
    variant_study_service: VariantStudyService,
    command_context: CommandContext,
    event_bus: IEventBus,
    task_service: ITaskService,
    core_config: Config,
):
    return StudyService(
        raw_study_service,
        variant_study_service,
        command_context,
        Mock(),
        Mock(),
        event_bus,
        Mock(),
        task_service,
        Mock(),
        core_config,
    )
