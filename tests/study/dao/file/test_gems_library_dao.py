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
from pathlib import Path

from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao

ASSETS_PATH = Path(__file__).parent.parent / "assets"


def test_default_case(dao_10_2: StudyDao) -> None:
    # We should not have a library for default studies
    library = dao_10_2.get_library()
    assert library is None


def test_library_reading_succeeds(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    lib_folder = dao.get_file_study().config.study_path / "input" / "model-libraries"
    lib_folder.mkdir(exist_ok=True)
    shutil.copy(ASSETS_PATH / "gems" / "libraries" / "8_1_simulator_nr_tests.yml", lib_folder / "my_library.yml")

    library = dao.get_library()
    assert library is not None
