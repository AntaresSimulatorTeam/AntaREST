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

from typing import Optional

from antarest.blobstore.service import IBlobService
from antarest.core.application import AppBuildContext
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
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from antarest.study.web.directory_blueprint import create_directory_routes
from antarest.study.web.raw_studies_blueprint import create_raw_study_routes
from antarest.study.web.studies_blueprint import create_study_routes
from antarest.study.web.study_data_blueprint import create_study_data_routes
from antarest.study.web.variant_blueprint import create_study_variant_routes
from antarest.study.web.xpansion_studies_blueprint import create_xpansion_routes


def build_study_service(
    app_ctxt: Optional[AppBuildContext],
    config: Config,
    user_service: LoginService,
    matrix_service: ISimpleMatrixService,
    blob_service: IBlobService,
    cache: ICache,
    file_transfer_manager: FileTransferManager,
    task_service: ITaskService,
    metadata_repository: Optional[StudyMetadataRepository] = None,
    variant_repository: Optional[VariantStudyRepository] = None,
    job_result_repository: Optional[JobResultRepository] = None,
    study_service: Optional[StudyService] = None,
    generator_matrix_constants: Optional[GeneratorMatrixConstants] = None,
    event_bus: IEventBus = DummyEventBusService(),
) -> StudyService:
    """
    Storage module linking dependencies.

    Args:
        app_ctxt: fastAPI application
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

    """

    mapper_factory = MatrixUriMapperFactory(matrix_service=matrix_service)
    study_factory = StudyFactory(matrix_mapper_factory=mapper_factory, cache=cache)
    metadata_repository = metadata_repository or StudyMetadataRepository(cache)
    variant_repository = variant_repository or VariantStudyRepository(cache)
    job_result_repository = job_result_repository or JobResultRepository()

    raw_study_service = RawStudyService(config=config, study_factory=study_factory, cache=cache)

    if not generator_matrix_constants:
        generator_matrix_constants = GeneratorMatrixConstants(matrix_service=matrix_service)
        generator_matrix_constants.init_constant_matrices()
    command_factory = CommandFactory(
        generator_matrix_constants=generator_matrix_constants, matrix_service=matrix_service, blob_service=blob_service
    )
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
    )

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

    if app_ctxt:
        add_study_routes(app_ctxt, study_service, directory_service, config)

    return study_service


def add_study_routes(
    app_ctxt: AppBuildContext, study_service: StudyService, directory_service: DirectoryService, config: Config
) -> None:
    api_root = app_ctxt.api_root
    api_root.include_router(create_study_routes(study_service, config))
    api_root.include_router(create_raw_study_routes(study_service, config))
    api_root.include_router(create_study_data_routes(study_service, config))
    api_root.include_router(
        create_study_variant_routes(
            study_service=study_service,
            config=config,
        )
    )
    api_root.include_router(create_xpansion_routes(study_service, config))
    api_root.include_router(create_directory_routes(directory_service, config))
