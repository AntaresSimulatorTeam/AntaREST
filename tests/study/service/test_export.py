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
import pytest

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.tasks.repository import TaskJobRepository
from antarest.core.tasks.service import TaskJobService
from antarest.eventbus.business.local_eventbus import LocalEventBus
from antarest.matrixstore.in_memory import InMemorySimpleMatrixService
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapperFactory
from antarest.study.directory_service import DirectoryService
from antarest.study.repository import DirectoryRepository, StudyMetadataRepository
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from conftest_services import SynchTaskService


@pytest.fixture
def service() -> StudyService:
    cache = LocalCache()
    matrix_service = InMemorySimpleMatrixService()
    mapper_factory = MatrixUriMapperFactory(matrix_service)
    study_factory = StudyFactory(mapper_factory, cache)
    raw_storage = RawStudyService(config, study_factory, cache, matrix_service)
    directory_service = DirectoryService(DirectoryRepository())
    study_repo = StudyMetadataRepository()
    user_service = None
    event_bus = LocalEventBus()
    task_repo = TaskJobRepository()
    # TODO
    task_service = TaskJobService(max_workers=1, task_repo, event_bus)
    variant_storage = VariantStudyService()

    def build_study_service(
        raw_study_service: RawStudyService,
        directory_service: DirectoryService,
        repository: StudyMetadataRepository,
        config: Config,
        user_service: LoginService = Mock(spec=LoginService),
        cache_service: ICache = Mock(spec=ICache),
        variant_study_service: VariantStudyService = Mock(spec=VariantStudyService),
        task_service: ITaskService = Mock(spec=ITaskService),
        event_bus: IEventBus = Mock(spec=IEventBus),
    ) -> StudyService:
        return StudyService(
            raw_study_service=raw_study_service,
            variant_study_service=variant_study_service,
            directory_service=directory_service,
            command_context=Mock(),
            user_service=user_service,
            repository=repository,
            job_result_repository=Mock(),
            event_bus=event_bus,
            task_service=task_service,
            file_transfer_manager=Mock(),
            cache_service=cache_service,
            config=config,
        )
