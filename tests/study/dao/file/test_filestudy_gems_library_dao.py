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

import pytest

from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from tests.study.dao.conftest import check_8_1_gems_library_integrity

ASSETS_PATH = Path(__file__).parent.parent / "assets"


def test_default_case(dao_10_2: StudyDao) -> None:
    # We should not have a library for default studies
    library = dao_10_2.get_library()
    assert library is None


def test_library_roundtrip(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    lib_folder = dao.get_file_study().config.study_path / "input" / "model-libraries"
    lib_folder.mkdir(exist_ok=True)
    shutil.copy(ASSETS_PATH / "gems" / "libraries" / "8_1_simulator_nr_tests.yml", lib_folder / "my_library.yml")

    library = dao.get_library()
    assert library is not None
    check_8_1_gems_library_integrity(library)

    # Remove the library file
    (lib_folder / "my_library.yml").unlink()
    assert dao.get_library() is None

    # Save the old content
    dao.save_library(library)
    library = dao.get_library()
    assert library is not None
    check_8_1_gems_library_integrity(library)


def test_several_libraries(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    lib_folder = dao.get_file_study().config.study_path / "input" / "model-libraries"
    lib_folder.mkdir(exist_ok=True)
    for file_name in ["library1.yml", "library2.yml", "library3.yml"]:
        shutil.copy(ASSETS_PATH / "gems" / "libraries" / "8_1_simulator_nr_tests.yml", lib_folder / file_name)

    with pytest.raises(ValueError, match="Found more than one gems library file for study"):
        dao.get_library()
