from typing import Optional

from fastapi import FastAPI

from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus, DummyEventBusService
from antarest.login.service import LoginService
from antarest.matrixstore.service import MatrixService
from antarest.study.storage.rawstudy.exporter_service import ExporterService
from antarest.study.storage.rawstudy.importer_service import ImporterService
from antarest.study.storage.rawstudy.patch_service import PatchService
from antarest.study.storage.rawstudy.raw_study_service import (
    RawStudyService,
)
from antarest.study.common.uri_resolver_service import (
    UriResolverService,
)
from antarest.study.storage.rawstudy.watcher import Watcher
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    StudyFactory,
)
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import StudyService
from antarest.study.web.areas_blueprint import create_study_area_routes
from antarest.study.web.raw_studies_blueprint import create_raw_study_routes
from antarest.study.web.studies_blueprint import create_study_routes
from antarest.study.web.variant_blueprint import create_study_variant_routes


def build_storage(
    application: FastAPI,
    config: Config,
    user_service: LoginService,
    matrix_service: MatrixService,
    cache: ICache,
    metadata_repository: Optional[StudyMetadataRepository] = None,
    storage_service: Optional[StudyService] = None,
    patch_service: Optional[PatchService] = None,
    event_bus: IEventBus = DummyEventBusService(),
) -> StudyService:
    """
    Storage module linking dependencies.

    Args:
        application: flask application
        config: server config
        user_service: user service facade
        matrix_service: matrix store service
        cache: cache service
        metadata_repository: used by testing to inject mock. Let None to use true instantiation
        storage_service: used by testing to inject mock. Let None to use true instantiation
        patch_service: used by testing to inject mock. Let None to use true instantiation
        event_bus: used by testing to inject mock. Let None to use true instantiation

    Returns:

    """

    path_resources = config.resources_path

    resolver = UriResolverService(config, matrix_service=matrix_service)
    study_factory = StudyFactory(
        matrix=matrix_service, resolver=resolver, cache=cache
    )
    metadata_repository = metadata_repository or StudyMetadataRepository()

    patch_service = patch_service or PatchService()

    study_service = RawStudyService(
        config=config,
        study_factory=study_factory,
        path_resources=path_resources,
        patch_service=patch_service,
        cache=cache,
    )
    importer_service = ImporterService(
        study_service=study_service,
        study_factory=study_factory,
    )
    exporter_service = ExporterService(
        study_service=study_service,
        study_factory=study_factory,
        config=config,
    )

    storage_service = storage_service or StudyService(
        study_service=study_service,
        importer_service=importer_service,
        exporter_service=exporter_service,
        user_service=user_service,
        repository=metadata_repository,
        event_bus=event_bus,
    )

    watcher = Watcher(config=config, service=storage_service)
    watcher.start()

    application.include_router(create_study_routes(storage_service, config))
    application.include_router(
        create_raw_study_routes(storage_service, config)
    )
    application.include_router(
        create_study_area_routes(storage_service, config)
    )
    application.include_router(
        create_study_variant_routes(storage_service, config)
    )

    return storage_service
