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

import os
import uuid
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

import pytest

from antarest.study.business.timeseries_config_management import TimeSeriesConfigManager, TSFormFields
from antarest.study.model import RawStudy
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from helpers import with_db_context


@pytest.fixture
def file_study_820(tmpdir: Path) -> FileStudy:
    cur_dir: Path = Path(__file__).parent
    study_path = Path(tmpdir / str(uuid.uuid4()))
    os.mkdir(study_path)
    with ZipFile(cur_dir / "assets" / f"empty_study_820.zip") as zip_output:
        zip_output.extractall(path=study_path)
    config = build(study_path, "1")
    return FileStudy(config, FileStudyTree(Mock(), config))


@with_db_context
def test_ts_field_values(
    file_study_820: FileStudy, raw_study_service: RawStudyService, variant_study_service: VariantStudyService
):
    # Checks default value
    assert file_study_820.tree.get(["settings", "generaldata", "general", "nbtimeseriesthermal"]) == 1

    # Prepares the test
    storage_service = StudyStorageService(raw_study_service, variant_study_service)
    config_manager = TimeSeriesConfigManager(storage_service)
    study = RawStudy(id="test", path=str(file_study_820.config.path))

    # Asserts the get method returns the right value
    assert config_manager.get_values(study) == TSFormFields(thermal=1)

    # Modifies the value and asserts the get takes the modification into account
    new_value = TSFormFields(thermal=2)
    config_manager.set_values(study, new_value)
    assert config_manager.get_values(study) == new_value
