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
import shutil
import time
import uuid
from pathlib import Path
from unittest.mock import Mock

import pytest
from helpers import with_admin_user, with_db_context
from sqlalchemy import create_engine

from antarest.blobstore.repository import BlobContentRepository
from antarest.blobstore.service import BlobService
from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.config import Config, StorageConfig, TaskConfig, WorkspaceConfig
from antarest.core.filetransfer.repository import FileDownloadRepository
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.eventbus import DummyEventBusService
from antarest.core.tasks.repository import TaskJobRepository
from antarest.core.tasks.service import TaskJobService
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.dbmodel import Base
from antarest.launcher.repository import JobResultRepository
from antarest.login.ldap import LdapService
from antarest.login.repository import (
    BotRepository,
    GroupRepository,
    IdentityRepository,
    RoleRepository,
    UserLdapRepository,
    UserRepository,
)
from antarest.login.service import LoginService
from antarest.matrixstore.in_memory import InMemorySimpleMatrixService
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapperFactory
from antarest.output.adapters import study_service_as_file_outputs_provider, study_service_as_studies_repository
from antarest.output.output_service import OutputService
from antarest.output.storage.file_output_storage import InStudyFileOutputStorage
from antarest.study.adapters import adapt_output_service_to_study_service
from antarest.study.directory_service import DirectoryService
from antarest.study.model import STUDY_VERSION_9_3
from antarest.study.repository import DirectoryRepository, StudyMetadataRepository
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.repository import VariantStudyRepository
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService

# TODO: remove that file


@pytest.fixture(scope="session")
def initial_db_file(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """
    Initializing the database schema is a costly operation: we perform it only once
    here for the test session, and then copy the database file to each integration test.
    """
    tmp_dir = tmp_path_factory.mktemp(basename=f"initial_db_file-{uuid.uuid4()}")
    db_path = tmp_dir / "db.sqlite"
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    return db_path


@pytest.fixture
def db_path(tmp_path: Path, initial_db_file: Path) -> Path:
    """
    We copy the base database file to the database file dedicated to each integration test.
    """
    db_path = tmp_path / "db.sqlite"
    shutil.copyfile(initial_db_file, db_path)
    return db_path


@pytest.fixture
def service(tmp_path: Path, db_path: Path) -> StudyService:
    t0 = time.time()

    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, echo=False)
    DBSessionMiddleware(None, custom_engine=engine)

    config = Config(
        tasks=TaskConfig(max_workers=1),
        storage=StorageConfig(workspaces={"default": WorkspaceConfig(path=tmp_path / "default")}),
    )

    cache = LocalCache()
    event_bus = DummyEventBusService()

    # matrix store setup
    matrix_service = InMemorySimpleMatrixService()
    matrix_constants = GeneratorMatrixConstants(matrix_service)
    matrix_constants.init_constant_matrices()
    mapper_factory = MatrixUriMapperFactory(matrix_service)

    # blobs
    blob_repo = BlobContentRepository(tmp_path / "blobs")
    blob_service = BlobService(blob_repo)

    # downloads
    download_repo = FileDownloadRepository()
    ftm = FileTransferManager(download_repo, event_bus, config)

    # Users
    identity_repo = IdentityRepository()
    bot_repo = BotRepository()
    user_repo = UserRepository()
    user_ldap_repo = UserLdapRepository()
    role_repo = RoleRepository()
    group_repo = GroupRepository()
    ldap_service = LdapService(config, user_ldap_repo, group_repo, role_repo)

    login_service = LoginService(
        user_repo=user_repo,
        identity_repo=identity_repo,
        bot_repo=bot_repo,
        group_repo=group_repo,
        role_repo=role_repo,
        ldap=ldap_service,
        event_bus=event_bus,
    )

    study_factory = StudyFactory(mapper_factory, cache)
    raw_storage = RawStudyService(config, study_factory, cache, matrix_service)
    directory_service = DirectoryService(DirectoryRepository())

    task_repo = TaskJobRepository()
    task_service = TaskJobService(config, task_repo, event_bus)

    command_factory = CommandFactory(matrix_constants, matrix_service, blob_service)
    variant_repo = VariantStudyRepository(cache)
    variant_storage = VariantStudyService(
        task_service=task_service,
        cache=cache,
        raw_study_service=raw_storage,
        command_factory=command_factory,
        study_factory=study_factory,
        repository=variant_repo,
        event_bus=event_bus,
        config=config,
        matrix_service=matrix_service,
    )

    command_context = CommandContext(
        generator_matrix_constants=matrix_constants,
        matrix_service=matrix_service,
        blob_service=blob_service,
    )

    job_repo = JobResultRepository()

    study_repo = StudyMetadataRepository(cache)
    study_service = StudyService(
        raw_study_service=raw_storage,
        variant_study_service=variant_storage,
        directory_service=directory_service,
        command_context=command_context,
        user_service=login_service,
        repository=study_repo,
        job_result_repository=job_repo,
        event_bus=event_bus,
        task_service=task_service,
        file_transfer_manager=ftm,
        cache_service=cache,
        config=config,
    )

    output_storage = InStudyFileOutputStorage(
        outputs_provider=study_service_as_file_outputs_provider(study_service), cache=cache, remote_executor=Mock()
    )
    output_service = OutputService(
        storage=output_storage,
        task_service=task_service,
        matrix_service=matrix_service,
        tmp_dir=tmp_path / "tmp",
        file_transfer_manager=ftm,
        studies_repository=study_service_as_studies_repository(study_service),
    )

    study_service.register_output_access(adapt_output_service_to_study_service(output_service))

    duration = time.time() - t0
    print(f"Study service setup took {duration:.3f} seconds")
    return study_service


@with_admin_user
@with_db_context
def test_service(service: StudyService) -> None:
    service.create_study("study", STUDY_VERSION_9_3, [])
