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


from antarest.blobstore.service import IBlobService
from antarest.core.config import Config
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import DummyEventBusService, IEventBus
from antarest.core.tasks.service import ITaskService
from antarest.launcher.repository import JobResultRepository
from antarest.login.service import LoginService
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapperFactory
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.directory_service import DirectoryService
from antarest.study.repository import DirectoryRepository, StudyMetadataRepository
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.repository import VariantStudyRepository
from antarest.study.storage.variantstudy.variant_database_storage import VariantDataBaseStudyStorage
from antarest.study.storage.variantstudy.variant_file_study_storage import VariantFileStudyStorage
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService


def build_study_service(
    config: Config,
    user_service: LoginService,
    matrix_service: ISimpleMatrixService,
    blob_service: IBlobService,
    cache: ICache,
    file_transfer_manager: FileTransferManager,
    task_service: ITaskService,
    metadata_repository: StudyMetadataRepository | None = None,
    variant_repository: VariantStudyRepository | None = None,
    job_result_repository: JobResultRepository | None = None,
    study_service: StudyService | None = None,
    generator_matrix_constants: GeneratorMatrixConstants | None = None,
    event_bus: IEventBus = DummyEventBusService(),
) -> tuple[StudyService, DirectoryService]:
    """
    Storage module linking dependencies.

    Args:
        config: server config
        user_service: user service facade
        matrix_service: matrix store service
        blob_service: blob store service
        cache: cache service
        file_transfer_manager: file transfer manager
        task_service: task job service
        metadata_repository: used by testing to inject mock. Let None to use true instantiation
        variant_repository: used by testing to inject mock. Let None to use true instantiation
        study_service: used by testing to inject mock. Let None to use true instantiation
        generator_matrix_constants: used by testing to inject mock. Let None to use true instantiation
        event_bus: used by testing to inject mock. Let None to use true instantiation

    Returns:
        A tuple of (StudyService, DirectoryService).
    """

    mapper_factory = MatrixUriMapperFactory(matrix_service=matrix_service)
    study_factory = StudyFactory(matrix_mapper_factory=mapper_factory, cache=cache)
    metadata_repository = metadata_repository or StudyMetadataRepository(cache)
    variant_repository = variant_repository or VariantStudyRepository(cache)
    job_result_repository = job_result_repository or JobResultRepository()

    raw_study_service = RawStudyService(
        config=config, study_factory=study_factory, cache=cache, matrix_service=matrix_service
    )

    if not generator_matrix_constants:
        generator_matrix_constants = GeneratorMatrixConstants(matrix_service=matrix_service)
        generator_matrix_constants.init_constant_matrices()
    command_factory = CommandFactory(
        generator_matrix_constants=generator_matrix_constants, matrix_service=matrix_service, blob_service=blob_service
    )

    variant_fs_storage = VariantFileStudyStorage(
        task_service=task_service,
        cache=cache,
        raw_study_service=raw_study_service,
        command_factory=command_factory,
        study_factory=study_factory,
        repository=variant_repository,
        event_bus=event_bus,
        config=config,
        matrix_service=matrix_service,
    )
    variant_db_storage = VariantDataBaseStudyStorage()
    variant_study_service = VariantStudyService(
        task_service=task_service,
        cache=cache,
        raw_study_service=raw_study_service,
        command_factory=command_factory,
        study_factory=study_factory,
        repository=variant_repository,
        event_bus=event_bus,
        config=config,
        matrix_service=matrix_service,
        variant_file_study_storage=variant_fs_storage,
        variant_database_study_storage=variant_db_storage,
    )
    variant_fs_storage.register_callable(variant_study_service.safe_generation)

    directory_service = DirectoryService(directory_repository=DirectoryRepository())

    study_service = study_service or StudyService(
        raw_study_service=raw_study_service,
        variant_study_service=variant_study_service,
        directory_service=directory_service,
        command_context=command_factory.command_context,
        user_service=user_service,
        repository=metadata_repository,
        job_result_repository=job_result_repository,
        event_bus=event_bus,
        file_transfer_manager=file_transfer_manager,
        task_service=task_service,
        cache_service=cache,
        config=config,
    )

    return study_service, directory_service
