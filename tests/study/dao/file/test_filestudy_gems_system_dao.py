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

import numpy as np
import pytest
from sqlalchemy.orm import Session

from antarest.core.exceptions import (
    GemsSystemAlreadyExists,
    GemsSystemIncorrectlyFormatted,
    GemsUnavailableForFileSystemStudies,
)
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader
from tests.study.dao.conftest import add_system_file_to_study_dao, build_db_dao_10_2, check_gems_system_integrity

ASSETS_PATH = Path(__file__).parent.parent / "assets"


def test_default_case(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    # We should not have a system for default studies
    assert filestudy_dao_v10_2.get_system() is None


def test_cannot_replace_system(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    add_system_file_to_study_dao(dao)

    system = dao.get_system()
    assert system is not None

    with pytest.raises(GemsSystemAlreadyExists, match="A system file already exists for study"):
        dao.save_system(system)


def test_system_roundtrip(filestudy_dao_v10_2: FileStudyTreeDao, matrix_service: ISimpleMatrixService) -> None:
    dao = filestudy_dao_v10_2
    add_system_file_to_study_dao(dao)

    # Data series files are loaded in the matrix store, the parameters then reference matrix ids
    system = dao.get_system()
    assert system is not None
    check_gems_system_integrity(system, matrix_service)

    _remove_system_file_for_study(dao)
    _remove_data_series_files_for_study(dao)
    assert dao.get_system() is None

    # Save the old content back: matrices are written as CSV files named after the component and parameter
    dao.save_system(system)
    data_series_folder = dao.get_file_study().config.study_path / "input" / "data-series"

    # todo: remove this test once optim-config.yml is handled in the DAO
    assert (dao.get_file_study().config.study_path / "input" / "optim-config.yml").exists()

    # As 2 parameters values point to the same matrix, we should have 2 CSV files only
    assert sorted(f.name for f in data_series_folder.iterdir()) == ["data_series_0.csv", "data_series_1.csv"]
    assert (data_series_folder / "data_series_0.csv").read_text().splitlines() == [
        "10.122",
        "12.344",
        "14.0",
        "16.566",
        "18.788",
        "20.5",
    ]

    yaml_system = YAMLReader().read(dao.get_file_study().config.study_path / "input" / "system.yml")["system"]
    components = yaml_system["components"]
    assert components[0]["parameters"][1]["value"] == "data_series_0"
    assert components[1]["parameters"][1]["value"] == "data_series_1"

    # Ensures we do not dump `None` values inside the YAML file
    for component in components:
        if "scenario-group" in component:
            assert component["scenario-group"] is not None

    saved_system = dao.get_system()
    assert saved_system is not None
    check_gems_system_integrity(saved_system, matrix_service)


def test_db_to_file_system_conversion(
    filestudy_dao_v10_2: FileStudyTreeDao, db_session: Session, matrix_service: ISimpleMatrixService
) -> None:
    db_dao = build_db_dao_10_2(db_session, matrix_service)
    add_system_file_to_study_dao(db_dao)
    db_system = db_dao.get_system()
    assert db_system is not None
    check_gems_system_integrity(db_system, matrix_service)

    file_dao = filestudy_dao_v10_2
    file_dao.save_system(db_system)

    fs_system = file_dao.get_system()
    assert fs_system is not None
    check_gems_system_integrity(fs_system, matrix_service)

    # Both studies point to matrices with the same content
    for db_component, fs_component in zip(db_system.components, fs_system.components):
        for db_parameter, fs_parameter in zip(db_component.parameters, fs_component.parameters):
            if db_parameter.time_dependent or db_parameter.scenario_dependent:
                db_matrix = matrix_service.get(str(db_parameter.value)).to_numpy()
                fs_matrix = matrix_service.get(str(fs_parameter.value)).to_numpy()
                assert np.array_equal(db_matrix, fs_matrix)
            else:
                assert db_parameter.value == fs_parameter.value


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


@pytest.mark.parametrize(
    "name",
    [
        "../data-series/max_load_values",
        "/etc/passwd",
        "sub/max_load_values",
        "max_load_values.tsv",
        "max_load_values\n",
        "ma x",
    ],
)
def test_data_series_name_must_be_a_plain_name(filestudy_dao_v10_2: FileStudyTreeDao, name: str) -> None:
    dao = filestudy_dao_v10_2
    _add_system_file_to_study(dao)
    system_file = dao.get_file_study().config.study_path / "input" / "system.yml"
    system_file.write_text(system_file.read_text().replace("value: max_load_values", f"value: {name!r}", 1))

    with pytest.raises(GemsSystemIncorrectlyFormatted, match="invalid data series name"):
        dao.get_system()


def test_data_series_file_exist_in_both_format(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    _add_system_file_to_study(dao)
    data_series_path = dao.get_file_study().config.study_path / "input" / "data-series"
    (data_series_path / "max_load_values.csv").touch()

    # Now we have both `max_load_values.csv` and `max_load_values.tsv` -> Should raise an error when reading the system

    msg = "The file 'max_load_values' inside study  exist in more than 1 format"
    with pytest.raises(GemsSystemIncorrectlyFormatted, match=msg):
        dao.get_system()


def _add_system_file_to_study(dao: FileStudyTreeDao) -> None:
    input_folder = dao.get_file_study().config.study_path / "input"
    shutil.copy(ASSETS_PATH / "gems" / "system" / "system.yml", input_folder / "system.yml")
    shutil.copytree(ASSETS_PATH / "gems" / "data-series", input_folder / "data-series", dirs_exist_ok=True)


def _remove_system_file_for_study(dao: FileStudyTreeDao) -> None:
    input_folder = dao.get_file_study().config.study_path / "input"
    (input_folder / "system.yml").unlink()


def _remove_data_series_files_for_study(dao: FileStudyTreeDao) -> None:
    shutil.rmtree(dao.get_file_study().config.study_path / "input" / "data-series")
