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

import io
import os
import shutil
from pathlib import Path
from unittest.mock import Mock

import py7zr
import pytest

from antarest.core.exceptions import BadArchiveContent, StudyValidationError
from antarest.study.model import DEFAULT_WORKSPACE_NAME, StudyAdditionalData
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.utils import fix_study_root
from tests.helpers import create_raw_study


@pytest.mark.unit_test
def test_import_study(tmp_path: Path) -> None:
    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    data = {"study": {"antares": {"version": 700}}}

    study = Mock()
    study.get.return_value = data
    study_factory = Mock()
    study_factory.create_from_fs.return_value = FileStudy(Mock(), study)

    study_service = RawStudyService(
        config=Mock(),
        study_factory=study_factory,
        cache=Mock(),
    )
    study_service.get = Mock()
    study_service.get_study_path = Mock()
    study_service.get.return_value = data

    # first test importing a study for an archived study with `.zip` format
    study_service.get_study_path.return_value = tmp_path / "other-study-zip"

    filepath_zip = shutil.make_archive(str(study_path.absolute()), "zip", study_path)
    shutil.rmtree(study_path)

    path_zip = Path(filepath_zip)

    md = create_raw_study(
        id="other-study-zip",
        workspace=DEFAULT_WORKSPACE_NAME,
        path=tmp_path / "other-study-zip",
        additional_data=StudyAdditionalData(),
        groups=["fake_group_1", "fake_group_2"],
    )
    with path_zip.open("rb") as input_file:
        md = study_service.import_study(md, input_file)
        assert md.path == f"{tmp_path}{os.sep}other-study-zip"
    # assert that importing file into a created study does not alter its group
    assert md.groups == ["fake_group_1", "fake_group_2"]

    shutil.rmtree(tmp_path / "other-study-zip")

    # second test for an archived study with a `.7z` format
    study_service.get_study_path.return_value = tmp_path / "other-study-7zip"

    study_path.mkdir()
    (study_path / "study.antares").touch()

    filepath_7zip = study_path.parent / f"{study_path.name}.7z"
    with py7zr.SevenZipFile(filepath_7zip, "w") as archive:
        archive.writeall(study_path, arcname="")

    shutil.rmtree(study_path)

    md = create_raw_study(
        id="other-study-7zip",
        workspace=DEFAULT_WORKSPACE_NAME,
        path=tmp_path / "other-study-7zip",
        additional_data=StudyAdditionalData(),
        groups=["fake_group_1", "fake_group_2"],
    )
    with filepath_7zip.open("rb") as input_file:
        md = study_service.import_study(md, input_file)
        assert md.path == f"{tmp_path}{os.sep}other-study-7zip"
    # assert that importing file into a created study does not alter its group
    assert md.groups == ["fake_group_1", "fake_group_2"]

    shutil.rmtree(tmp_path / "other-study-7zip")

    # test for an unsupported archive format
    with pytest.raises(BadArchiveContent, match="Unsupported archive format"):
        study_service.import_study(md, io.BytesIO(b""))


@pytest.mark.unit_test
def test_fix_root(tmp_path: Path):
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
