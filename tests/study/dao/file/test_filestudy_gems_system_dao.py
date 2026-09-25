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

from antarest.core.exceptions import GemsSystemAlreadyExists, GemsUnavailableForFileSystemStudies
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from tests.study.dao.conftest import check_gems_system_integrity

ASSETS_PATH = Path(__file__).parent.parent / "assets"


def test_default_case(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    # We should not have a system for default studies
    assert filestudy_dao_v10_2.get_system() is None

    with pytest.raises(GemsUnavailableForFileSystemStudies):
        filestudy_dao_v10_2.get_components()


def test_cannot_replace_system(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    _add_system_file_to_study(dao)

    system = dao.get_system()
    assert system is not None

    with pytest.raises(GemsSystemAlreadyExists, match="A system file already exists for study"):
        dao.save_system(system)


def test_system_roundtrip(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    _add_system_file_to_study(dao)

    system = dao.get_system()
    assert system is not None
    check_gems_system_integrity(system)

    _remove_system_file_for_study(dao)
    assert dao.get_system() is None

    # Save the old content back
    dao.save_system(system)
    saved_system = dao.get_system()
    assert saved_system is not None
    check_gems_system_integrity(saved_system)


def test_should_not_access_system_components(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    _add_system_file_to_study(dao)

    with pytest.raises(
        GemsUnavailableForFileSystemStudies,
        match=f"Gems is unavailable for FileSystem studies, but study {dao.get_file_study().config.study_id} tried to use it.",
    ):
        dao.get_components()

    with pytest.raises(
        GemsUnavailableForFileSystemStudies,
        match=f"Gems is unavailable for FileSystem studies, but study {dao.get_file_study().config.study_id} tried to use it.",
    ):
        dao.save_components([])


def _add_system_file_to_study(dao: FileStudyTreeDao) -> None:
    input_folder = dao.get_file_study().config.study_path / "input"
    shutil.copy(ASSETS_PATH / "gems" / "system" / "system.yml", input_folder / "system.yml")


def _remove_system_file_for_study(dao: FileStudyTreeDao) -> None:
    input_folder = dao.get_file_study().config.study_path / "input"
    (input_folder / "system.yml").unlink()
