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

from antarest.study.business.model.gems.data_series import GemsDataSeries
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao

ASSETS_PATH = Path(__file__).parent.parent / "assets"


def test_default_case(dao_10_2: StudyDao) -> None:
    # We should not have any data series for default studies
    data_series = dao_10_2.get_data_series()
    assert data_series == []


def test_data_series_roundtrip(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    ds_folder = dao.get_file_study().config.study_path / "input" / "data-series"
    ds_folder.mkdir(exist_ok=True)
    shutil.copy(ASSETS_PATH / "gems" / "data-series" / "max_load_values.csv", ds_folder / "max_load_values.csv")

    data_series = dao.get_data_series()
    assert len(data_series) == 1
    check_data_series_integrity(data_series)

    # Remove the data series file
    (ds_folder / "max_load_values.csv").unlink()
    assert dao.get_data_series() == []

    # Save the old content
    dao.save_data_series(data_series)
    data_series = dao.get_data_series()
    assert data_series is not None
    check_data_series_integrity(data_series)


def check_data_series_integrity(data_series: list[GemsDataSeries]) -> None:
    assert len(data_series) == 1
    assert data_series[0].id == "max_load_values"
    values = data_series[0].values

    assert len(values) == 24
    for i in range(24):
        assert values[i][0] == 10 + i * 2
