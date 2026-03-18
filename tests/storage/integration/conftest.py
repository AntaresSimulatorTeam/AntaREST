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

import datetime
import shutil
import zipfile
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

import py7zr
import pytest

from antarest.blobstore.repository import BlobContentRepository
from antarest.blobstore.service import BlobService
from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.config import (
    CacheConfig,
    Config,
    InternalMatrixFormat,
    SecurityConfig,
    StorageConfig,
    WorkspaceConfig,
)
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.remote.remote_executor import RemoteWorkerExecutor
from antarest.core.tasks.service import ITaskService
from antarest.login.model import User
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapperFactory
from antarest.matrixstore.repository import MatrixContentRepository
from antarest.matrixstore.service import ISimpleMatrixService, SimpleMatrixService
from antarest.output.adapters import study_service_as_file_outputs_provider, study_service_as_studies_repository
from antarest.output.output_service import OutputService
from antarest.output.storage.file_output_storage import InStudyFileOutputStorage
from antarest.output.storage.output_storage import IOutputStorage
from antarest.study.adapters import adapt_output_service_to_study_service
from antarest.study.directory_service import DirectoryService
from antarest.study.model import DEFAULT_WORKSPACE_NAME
from antarest.study.repository import DirectoryRepository, StudyMetadataRepository
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.repository import VariantStudyRepository
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from tests.helpers import create_raw_study

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def _build_study_service(
    config: Config,
    user_service,
    matrix_service: ISimpleMatrixService,
    blob_service,
    cache: ICache,
    file_transfer_manager,
    task_service: ITaskService,
    metadata_repository=None,
    variant_repository=None,
    job_result_repository=None,
    generator_matrix_constants=None,
    event_bus=None,
) -> StudyService:
    from antarest.core.interfaces.eventbus import DummyEventBusService

    event_bus = event_bus or DummyEventBusService()
    mapper_factory = MatrixUriMapperFactory(matrix_service=matrix_service)
    study_factory = StudyFactory(matrix_mapper_factory=mapper_factory, cache=cache)
    metadata_repository = metadata_repository or StudyMetadataRepository(cache)
    variant_repository = variant_repository or VariantStudyRepository(cache)
    job_result_repository = job_result_repository or Mock()

    raw_study_service = RawStudyService(
        config=config, study_factory=study_factory, cache=cache, matrix_service=matrix_service
    )

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

    return StudyService(
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


def _build_output_service(
    study_service: StudyService,
    cache: ICache,
    task_service: ITaskService,
    filetransfer_service: FileTransferManager,
    event_bus: IEventBus,
    config: Config,
    matrix_service: ISimpleMatrixService,
) -> OutputService:
    remote_executor = RemoteWorkerExecutor(event_bus, config)
    file_output_storage = InStudyFileOutputStorage(
        outputs_provider=study_service_as_file_outputs_provider(study_service),
        cache=cache,
        remote_executor=remote_executor,
    )
    storages: list[IOutputStorage] = [file_output_storage]

    output_service = OutputService(
        studies_repository=study_service_as_studies_repository(study_service),
        storages=storages,
        task_service=task_service,
        file_transfer_manager=filetransfer_service,
        matrix_service=matrix_service,
        tmp_dir=config.storage.tmp_dir,
    )

    study_service.register_output_access(adapt_output_service_to_study_service(output_service))

    return output_service


@pytest.fixture(scope="session")
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


@pytest.fixture
def sta_mini_seven_zip_path(project_path: Path, sta_mini_zip_path: Path) -> Path:
    target = project_path / "examples/studies/STA-mini.7z"
    if target.is_file():
        return target
    with zipfile.ZipFile(sta_mini_zip_path, "r") as zf:
        zf.extractall(sta_mini_zip_path.parent)
    extracted_dir_path = sta_mini_zip_path.parent / "STA-mini"
    with py7zr.SevenZipFile(target, "w") as szf:
        szf.writeall(extracted_dir_path, arcname="")
    shutil.rmtree(extracted_dir_path)
    return target


@pytest.fixture
def services(tmp_path: Path, project_path: Path, sta_mini_zip_path: Path) -> tuple[StudyService, OutputService, Config]:
    path_studies = tmp_path / "studies"

    path_resources = project_path / "resources"

    with ZipFile(sta_mini_zip_path) as zip_output:
        zip_output.extractall(path=path_studies)

    (path_studies / "STA-mini").rename(path_studies / UUID)

    # noinspection PyArgumentList
    md = create_raw_study(
        id=UUID,
        name="STA-mini",
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(path_studies / UUID),
        created_at=datetime.datetime.fromtimestamp(1480683452),
        updated_at=datetime.datetime.fromtimestamp(1602678639),
        version="700",
        author="Andrea SGATTONI",
        horizon=2030,
    )
    repo = Mock()
    # noinspection PyArgumentList
    repo.get.side_effect = lambda name: create_raw_study(
        id=name,
        name=name,
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(path_studies / name),
        created_at=datetime.datetime.fromtimestamp(1480683452),
        updated_at=datetime.datetime.fromtimestamp(1602678639),
        version="700",
    )
    repo.get_all.return_value = [md]

    variant_repo = Mock()
    variant_repo.get_children.return_value = []

    config = Config(
        resources_path=path_resources,
        security=SecurityConfig(disabled=True),
        cache=CacheConfig(),
        storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=path_studies)}),
    )

    task_service_mock = Mock(spec=ITaskService)
    user_service = Mock()
    # noinspection PyArgumentList
    user_service.get_user.return_value = User(id=0, name="test")

    job_result_repository = Mock()
    job_result_repository.find_by_study.return_value = []

    # Matrices
    matrix_path = tmp_path / "matrices"
    matrix_path.mkdir()
    matrix_content_repository = MatrixContentRepository(bucket_dir=matrix_path, format=InternalMatrixFormat.TSV)
    matrix_service = SimpleMatrixService(matrix_content_repository=matrix_content_repository)

    # Blob
    blob_path = tmp_path / "blob"
    blob_path.mkdir()
    blob_content_repository = BlobContentRepository(bucket_dir=blob_path)
    blob_service = BlobService(blob_content_repository=blob_content_repository)

    cache = LocalCache(config=config.cache)

    # Final object
    study_service = _build_study_service(
        config=config,
        cache=cache,
        file_transfer_manager=Mock(),
        task_service=task_service_mock,
        user_service=user_service,
        matrix_service=matrix_service,
        blob_service=blob_service,
        metadata_repository=repo,
        variant_repository=variant_repo,
        job_result_repository=job_result_repository,
    )

    output_service = _build_output_service(
        study_service=study_service,
        config=config,
        cache=cache,
        event_bus=study_service.event_bus,
        task_service=task_service_mock,
        filetransfer_service=Mock(),
        matrix_service=matrix_service,
    )

    return study_service, output_service, config


@pytest.fixture
def storage_service(services: tuple[StudyService, OutputService, Config]) -> StudyService:
    return services[0]
