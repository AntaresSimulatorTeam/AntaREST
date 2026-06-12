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

import io
import os
import shutil
from pathlib import Path
from unittest.mock import Mock

import py7zr
import pytest

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.exceptions import StudyImportFailed, StudyValidationError
from antarest.login.model import User
from antarest.study.model import StorageMode
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.utils import fix_study_root
from tests.helpers import with_admin_user, with_db_context


@with_db_context
@with_admin_user
def test_import_study(tmp_path: Path, study_service: StudyService, empty_study_930: FileStudy) -> None:
    # Set Up
    file_study = empty_study_930
    study_path = file_study.config.study_path
    (tmp_path / "internal_studies").mkdir()
    output_access_mock = Mock()
    study_service.register_output_access(output_access_mock)
    study_service.user_service.get_user.return_value = User(id=1, name="admin")
    study_service.repository = StudyMetadataRepository(LocalCache())

    # .zip part
    filepath_zip = shutil.make_archive(str(study_path.absolute()), "zip", study_path)
    path_zip = Path(filepath_zip)

    with path_zip.open("rb") as input_file:
        study_id = study_service.import_study(
            input_file, group_ids=["admin"], directory="", storage_mode=StorageMode.FILESYSTEM
        )

    study = study_service.get_study(study_id)

    # Asserts the group is correctly set
    assert len(study.groups) == 1
    assert study.groups[0].id == "admin"

    # Checks other attributes
    assert study.archived is False
    assert study.directory is None  # We did not ask for one
    assert study.name == "empty_study"
    assert study.owner.name == "admin"
    assert study.storage_mode == StorageMode.FILESYSTEM

    # .7z part
    filepath_7zip = study_path.parent / f"{study_path.name}.7z"
    with py7zr.SevenZipFile(filepath_7zip, "w") as archive:
        archive.writeall(study_path, arcname="")

    with filepath_7zip.open("rb") as input_file:
        study_id = study_service.import_study(input_file, group_ids=[], directory="", storage_mode=StorageMode.DATABASE)

    # Checks study attributes
    study = study_service.get_study(study_id)
    assert study.storage_mode == StorageMode.DATABASE
    assert study.groups == []

    # test for an unsupported archive format
    with pytest.raises(StudyImportFailed, match="Unsupported archive format"):
        study_service.import_study(io.BytesIO(b""), [], "", StorageMode.FILESYSTEM)


def test_fix_root(tmp_path: Path) -> None:
    name = "my-study"
    study_path = tmp_path / name
    study_nested_root = study_path / "nested" / "real_root"
    os.makedirs(study_nested_root)
    (study_nested_root / "antares.study").touch()
    # when the study path is a single file
    with pytest.raises(StudyValidationError):
        fix_study_root(study_nested_root / "antares.study")

    shutil.rmtree(study_path)
    study_path = tmp_path / name
    study_nested_root = study_path / "nested" / "real_root"
    os.makedirs(study_nested_root)
    (study_nested_root / "antares.study").touch()
    os.mkdir(study_nested_root / "input")

    fix_study_root(study_path)
    study_files = os.listdir(study_path)
    assert len(study_files) == 2
    assert "antares.study" in study_files and "input" in study_files

    shutil.rmtree(study_path)
