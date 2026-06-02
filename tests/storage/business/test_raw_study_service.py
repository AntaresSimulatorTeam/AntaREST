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
import re
from pathlib import Path, PurePosixPath
from unittest.mock import Mock
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from antares.study.version import StudyVersion

from antarest.blobstore.service import BlobService
from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.exceptions import StudyDeletionNotAllowed
from antarest.core.interfaces.cache import CacheConstants, ICache
from antarest.core.model import PublicMode
from antarest.core.serde.ini_reader import read_ini
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group, Identity
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.output.storage.file.storage import (
    FileStudyOutputs,
    IFileOutputsProvider,
    InStudyFileOutputStorage,
)
from antarest.study.dao.file.file_study_factory_dao import FileStudyDaoFactory
from antarest.study.main import build_study_service
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy, StudyMetadataCopy
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.utils import StudyMetadataCreation
from tests.conftest import build_metadata_creation_object_from_study
from tests.helpers import create_raw_study, create_variant_study, with_admin_user, with_db_context


def build_config(
    study_path: Path,
    workspace_name: str = DEFAULT_WORKSPACE_NAME,
    allow_deletion: bool = False,
) -> Config:
    return Config(
        storage=StorageConfig(
            workspaces={workspace_name: WorkspaceConfig(path=study_path)},
            allow_deletion=allow_deletion,
        )
    )


@with_db_context
def test_create_file_study_dao(tmp_path: Path, project_path: Path) -> None:
    # Create the `Mock` objects
    study = Mock()
    data = {"antares": {"caption": None}}
    study.get.return_value = data

    study_factory = Mock()
    study_factory.create_from_fs.return_value = FileStudy(Mock(), study)
    config = build_config(tmp_path)
    raw_study_service = RawStudyService(config, Mock(), study_factory, Mock(), StudyMetadataRepository(Mock()))

    # Add the `RawStudy` in the database
    raw_study = create_raw_study(
        id="study1",
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(config.get_workspace_path() / "study1"),
        version="720",
        created_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
        updated_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
        author="john.doe",
    )
    db.session.add(raw_study)
    db.session.commit()

    # Tests the DAO creation method
    factory = FileStudyDaoFactory(Mock(), study_factory, Mock(), raw_study_service.get_study_paths)
    metadata = StudyMetadataCreation(
        id=raw_study.id,
        version=StudyVersion.parse(raw_study.version),
        managed=True,
        name=raw_study.name,
        author=raw_study.author,
        editor=raw_study.editor,
        created_at=raw_study.created_at,
        updated_at=raw_study.updated_at,
    )
    factory.create_study_dao(metadata)

    assert raw_study.path == str(tmp_path / "study1")
    path_study = tmp_path / raw_study.id
    assert path_study.exists()

    path_study_antares_infos = path_study / "study.antares"
    assert path_study_antares_infos.is_file()


@with_db_context
def test_create_study_versions(tmp_path: str, project_path: Path) -> None:
    path_studies = Path(tmp_path)

    study = Mock()
    data = {"antares": {"caption": None}}
    study.get.return_value = data

    study_factory = Mock()
    study_factory.create_from_fs.return_value = FileStudy(Mock(), study)
    config = build_config(path_studies)
    raw_study_service = RawStudyService(config, Mock(), study_factory, Mock(), StudyMetadataRepository(Mock()))

    def create_study(version: str) -> RawStudy:
        raw_study = create_raw_study(
            id=f"study{version}",
            workspace=DEFAULT_WORKSPACE_NAME,
            path=str(config.get_workspace_path() / f"study{version}"),
            version=version,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            author="john.doe",
        )
        db.session.add(raw_study)
        db.session.commit()
        metadata = build_metadata_creation_object_from_study(raw_study)
        FileStudyDaoFactory(Mock(), study_factory, Mock(), raw_study_service.get_study_paths).create_study_dao(metadata)
        return raw_study

    md700 = create_study("700")
    md710 = create_study("710")
    md720 = create_study("720")
    md803 = create_study("800")
    md810 = create_study("810")
    md850 = create_study("850")

    path_study = path_studies / md700.id
    general_data_file = path_study / "settings" / "generaldata.ini"
    general_data = general_data_file.read_text()
    assert re.search("^link-type = local", general_data, flags=re.MULTILINE) is not None
    assert (
        re.search(
            "^initial-reservoir-levels = cold start",
            general_data,
            flags=re.MULTILINE,
        )
        is not None
    )

    path_study = path_studies / md710.id
    general_data_file = path_study / "settings" / "generaldata.ini"
    general_data = general_data_file.read_text()
    assert re.search("^thematic-trimming = false", general_data, flags=re.MULTILINE) is not None
    assert re.search("^geographic-trimming = false", general_data, flags=re.MULTILINE) is not None

    path_study = path_studies / md720.id
    general_data_file = path_study / "settings" / "generaldata.ini"
    general_data = general_data_file.read_text()
    assert (
        re.search(
            "^include-unfeasible-problem-behavior = error-verbose",
            general_data,
            flags=re.MULTILINE,
        )
        is not None
    )

    path_study = path_studies / md803.id
    general_data_file = path_study / "settings" / "generaldata.ini"
    general_data = general_data_file.read_text()
    assert re.search("^custom-ts-numbers = false", general_data, flags=re.MULTILINE) is None
    assert re.search("^custom-scenario = false", general_data, flags=re.MULTILINE) is not None
    assert (
        re.search(
            "^include-exportstructure = false",
            general_data,
            flags=re.MULTILINE,
        )
        is not None
    )
    assert (
        re.search(
            "^hydro-heuristic-policy = accommodate rule curves",
            general_data,
            flags=re.MULTILINE,
        )
        is not None
    )

    path_study = path_studies / md810.id
    general_data_file = path_study / "settings" / "generaldata.ini"
    general_data = general_data_file.read_text()
    assert (
        re.search(
            "^renewable-generation-modelling = false",
            general_data,
            flags=re.MULTILINE,
        )
        is None
    )

    path_study = path_studies / md850.id
    general_data_file = path_study / "settings" / "generaldata.ini"
    general_data = general_data_file.read_text()
    assert (
        re.search(
            "^price-taking-order = DENS",
            general_data,
            flags=re.MULTILINE,
        )
        is not None
    )
    assert (
        re.search(
            "^include-hurdle-cost-csr = false",
            general_data,
            flags=re.MULTILINE,
        )
        is not None
    )
    assert (
        re.search(
            "^check-csr-cost-function = false",
            general_data,
            flags=re.MULTILINE,
        )
        is not None
    )
    assert (
        re.search(
            "^threshold-initiate-curtailment-sharing-rule = 1.0",
            general_data,
            flags=re.MULTILINE,
        )
        is not None
    )
    assert (
        re.search(
            "^threshold-display-local-matching-rule-violations = 0.0",
            general_data,
            flags=re.MULTILINE,
        )
        is not None
    )
    assert (
        re.search(
            "^threshold-csr-variable-bounds-relaxation = 7",
            general_data,
            flags=re.MULTILINE,
        )
        is not None
    )


@with_db_context
@with_admin_user
def test_copy_study(empty_study_930: FileStudy, study_service: StudyService) -> None:
    file_study = empty_study_930
    study_path = file_study.config.study_path
    study_id = file_study.config.study_id

    study = create_raw_study(id=study_id, path=str(study_path), public_mode=PublicMode.NONE, groups=[])

    # Initialize arguments for the copy method
    destination = PurePosixPath("myfolder/subfolder")
    groups = [Group(id="my_grp", name="my_grp")]
    admin = Identity(id=1, name="admin", type="users")

    # Copy the study
    metadata = StudyMetadataCopy(name="new_name", groups=groups, owner=admin, directory_id=None, folder=destination)
    new_study = study_service.storage_service.raw_study_service.copy(study, metadata)

    # Check the new study attributes
    assert new_study.path == str(study_path.parent / "internal_studies" / new_study.id)
    assert new_study.public_mode == PublicMode.NONE
    assert len(new_study.groups) == 1
    assert new_study.groups[0].id == "my_grp"
    assert new_study.folder == f"{destination.as_posix()}/{new_study.id}"
    assert new_study.name == "new_name"
    assert new_study.owner.name == "admin"

    # Checks study.antares is correctly updated
    study_path = study_path.parent / "internal_studies" / new_study.id
    assert study_path.exists()
    assert read_ini(study_path / "study.antares")["antares"]["caption"] == "new_name"


def test_zipped_output(tmp_path: Path) -> None:
    # Setup
    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()
    cache = Mock()
    study_service = RawStudyService(
        config=build_config(tmp_path, workspace_name="foo", allow_deletion=False),
        cache=cache,
        study_factory=Mock(),
        command_context=Mock(),
        repository=Mock(),
    )

    md = create_raw_study(id=name, workspace="foo", path=str(study_path))

    zipped_output = tmp_path / "output.zip"
    with ZipFile(zipped_output, "w", ZIP_DEFLATED) as output_data:
        output_data.writestr(
            "info.antares-output",
            """[general]
version = 700
name = 11mc
mode = Economy
date = 2020.09.07 - 16:15
title = 2020.09.07 - 16:15
timestamp = 1599488150
        """,
        )

    class OutputsProvider(IFileOutputsProvider):
        def get_outputs(self, study_id: str) -> FileStudyOutputs:
            return FileStudyOutputs(
                get_file_study=lambda: study_service.get_raw(md),
                outputs_path=study_path / "output",
                study_workspace=DEFAULT_WORKSPACE_NAME,
            )

    output_storage = InStudyFileOutputStorage(
        OutputsProvider(), cache=Mock(), remote_executor=Mock(), repository=Mock()
    )

    # Test
    expected_output_name = "20200907-1615eco-11mc"
    output_name = output_storage.import_output(name, zipped_output)
    if output_name != expected_output_name:
        # because windows sucks...
        expected_output_name = "20200907-1415eco-11mc"
    assert output_name == expected_output_name
    assert (study_path / "output" / (expected_output_name + ".zip")).exists()

    output_storage.unarchive_study_output(name, expected_output_name)
    assert (study_path / "output" / expected_output_name).exists()
    assert not (study_path / "output" / (expected_output_name + ".zip")).exists()

    output_storage.archive_study_output(name, expected_output_name)
    assert not (study_path / "output" / expected_output_name).exists()
    assert (study_path / "output" / (expected_output_name + ".zip")).exists()
    output_storage.delete_output(name, output_name)
    assert not (study_path / "output" / (expected_output_name + ".zip")).exists()


def _create_fake_study(path: Path) -> Path:
    name = "my-study"
    study_path = path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()
    return study_path


def _build_study_service(config: Config, cache: ICache, repo: StudyMetadataRepository) -> StudyService:
    study_service, _ = build_study_service(
        config,
        matrix_service=Mock(spec=ISimpleMatrixService),
        cache=cache,
        metadata_repository=repo,
        file_transfer_manager=Mock(),
        task_service=Mock(),
        user_service=Mock(),
        event_bus=Mock(),
        blob_service=Mock(spec=BlobService),
    )
    return study_service


@with_admin_user
@with_db_context
def test_delete_raw_study(tmp_path: Path) -> None:
    # Set Up
    cache = Mock(spec=ICache)
    cache.get.return_value = None

    study_path = _create_fake_study(tmp_path)
    name = study_path.name

    raw_study = create_raw_study(id=name, workspace="foo", path=str(study_path), groups=[])

    config = build_config(tmp_path, workspace_name="foo", allow_deletion=False)
    repo = Mock()
    repo.get.return_value = raw_study
    study_service = _build_study_service(config, cache, repo)

    # Deletion is forbidden
    with pytest.raises(StudyDeletionNotAllowed):
        study_service.delete_study(raw_study.id, children=False)

    # Allow deletion
    study_service.config = build_config(tmp_path, workspace_name="foo", allow_deletion=True)
    fake_output_access = Mock()
    fake_output_access.list_outputs.return_value = []
    study_service.register_output_access(fake_output_access)

    study_service.delete_study(raw_study.id, children=False)

    # Ensures the cache was called
    study_service.storage_service.raw_study_service.cache.invalidate_all.assert_called_once_with(
        [
            f"{CacheConstants.RAW_STUDY}/{name}",
            f"{CacheConstants.STUDY_FACTORY}/{name}",
        ]
    )
    assert not study_path.exists()


@with_admin_user
@with_db_context
def test_delete_variant_study(tmp_path: Path) -> None:
    # Set Up
    cache = Mock(spec=ICache)
    cache.get.return_value = None

    config = build_config(tmp_path, workspace_name="foo", allow_deletion=True)
    repo = Mock()
    study_service = _build_study_service(config, cache, repo)

    study_path = _create_fake_study(tmp_path)
    name = study_path.name

    variant_study = create_variant_study(id=name, path=str(study_path))
    repo.get.return_value = variant_study

    fake_output_access = Mock()
    fake_output_access.list_outputs.return_value = []
    study_service.register_output_access(fake_output_access)

    # Delete study
    study_service.delete_study(variant_study.id, children=False)

    cache.invalidate_all.assert_called_once_with(
        [
            f"{CacheConstants.RAW_STUDY}/{name}",
            f"{CacheConstants.STUDY_FACTORY}/{name}",
        ]
    )
    assert not study_path.exists()


def test_update_name_and_version_from_raw(tmp_path: Path) -> None:
    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    raw_study = create_raw_study(
        id=name,
        name=name,
        version="700",
        workspace="foo",
        path=str(study_path),
    )
    study_factory = Mock()
    study_tree_mock = Mock()
    study_factory.create_from_fs.return_value = FileStudy(Mock(), study_tree_mock)

    study_service = RawStudyService(
        config=build_config(tmp_path, workspace_name="foo"),
        cache=Mock(),
        study_factory=study_factory,
        command_context=Mock(),
        repository=Mock(),
    )

    study_tree_mock.get.side_effect = [
        {"caption": name, "version": "700"},
        {"caption": "new_name", "version": "700"},
        {"caption": "new_name", "version": "800"},
    ]

    assert not study_service.update_name_and_version_from_raw_meta(raw_study)

    assert study_service.update_name_and_version_from_raw_meta(raw_study)
    assert raw_study.name == "new_name"
    assert study_service.update_name_and_version_from_raw_meta(raw_study)
    assert raw_study.name == "new_name"
    assert raw_study.version == "800"
