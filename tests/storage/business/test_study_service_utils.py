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

import datetime
import tarfile
from hashlib import md5
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock
from zipfile import ZipFile

import numpy as np
import pytest

from antarest.study.model import (
    ExportFormat,
    MatrixAggregationResultDTO,
    MatrixIndex,
    StudyDownloadLevelDTO,
    StudyDownloadType,
    TimeSerie,
    TimeSeriesData,
)
from antarest.study.storage.study_download_utils import StudyDownloader
from antarest.study.storage.utils import DAY_NAMES, get_start_date


def test_output_downloads_export(tmp_path: Path):
    matrix = MatrixAggregationResultDTO(
        index=MatrixIndex(start_date="2000-01-01 00:00:00"),
        data=[
            TimeSeriesData(
                name="a1",
                type=StudyDownloadType.AREA,
                data={
                    "1": [
                        TimeSerie(name="A", unit="", data=np.array([1, 2, 3, 4], dtype=np.float64)),
                        TimeSerie(name="B", unit="", data=np.array([5, 6, 7, 8], dtype=np.float64)),
                    ],
                    "2": [
                        TimeSerie(name="A", unit="", data=np.array([10, 11, 12, 13], dtype=np.float64)),
                        TimeSerie(name="B", unit="", data=np.array([14, None, None, 15], dtype=np.float64)),
                    ],
                },
            ),
            TimeSeriesData(
                name="a2",
                type=StudyDownloadType.AREA,
                data={
                    "1": [
                        TimeSerie(name="A", unit="", data=np.array([16, 17, 18, 19], dtype=np.float64)),
                        TimeSerie(name="B", unit="", data=np.array([20, 21, 22, 23], dtype=np.float64)),
                    ],
                    "2": [
                        TimeSerie(name="A", unit="", data=np.array([24, None, 25, 26], dtype=np.float64)),
                        TimeSerie(name="B", unit="", data=np.array([27, 28, 29, 30], dtype=np.float64)),
                    ],
                },
            ),
        ],
        warnings=[],
    )
    zip_file = tmp_path / "output.zip"
    StudyDownloader.export(matrix, ExportFormat.ZIP, zip_file)
    with ZipFile(zip_file) as zip_input:
        assert zip_input.namelist() == ["a1.csv", "a2.csv"]
        print(zip_input.read("a1.csv"))
        assert md5(zip_input.read("a1.csv")).hexdigest() == "e183e79f2184d6f6dacb8ad215cb056c"
        assert md5(zip_input.read("a2.csv")).hexdigest() == "c007db83f2769e6128e0f8c6b04d43eb"

    tar_file = tmp_path / "output.tar.gz"
    StudyDownloader.export(matrix, ExportFormat.TAR_GZ, tar_file)
    with tarfile.open(tar_file, mode="r:gz") as tar_input:
        assert tar_input.getnames() == ["a1.csv", "a2.csv"]
        data = tar_input.extractfile("a1.csv").read()
        assert md5(data).hexdigest() == "e183e79f2184d6f6dacb8ad215cb056c"
        data = tar_input.extractfile("a2.csv").read()
        assert md5(data).hexdigest() == "c007db83f2769e6128e0f8c6b04d43eb"


@pytest.mark.parametrize(
    "config,level,expected",
    [
        (
            {
                "first-month-in-year": "january",
                "january.1st": "Monday",
                "leapyear": True,
                "first.weekday": "Monday",
                "simulation.start": 1,
                "simulation.end": 354,
            },
            StudyDownloadLevelDTO.WEEKLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2024, 1, 1)),
                steps=51,
                first_week_size=7,
                level=StudyDownloadLevelDTO.WEEKLY,
            ),
        ),
        (
            {
                "first-month-in-year": "january",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 1,
                "simulation.end": 354,
            },
            StudyDownloadLevelDTO.WEEKLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2018, 1, 1)),
                steps=51,
                first_week_size=7,
                level=StudyDownloadLevelDTO.WEEKLY,
            ),
        ),
        (
            {
                "first-month-in-year": "july",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Wednesday",
                "simulation.start": 5,
                "simulation.end": 340,
            },
            StudyDownloadLevelDTO.WEEKLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 7, 5)),
                steps=48,
                first_week_size=7,
                level=StudyDownloadLevelDTO.WEEKLY,
            ),
        ),
        (
            {
                "first-month-in-year": "july",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 1,
                "simulation.end": 200,
            },
            StudyDownloadLevelDTO.MONTHLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 7, 1)),
                steps=7,
                first_week_size=2,
                level=StudyDownloadLevelDTO.MONTHLY,
            ),
        ),
        (
            {
                "first-month-in-year": "july",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 1,
                "simulation.end": 100,
            },
            StudyDownloadLevelDTO.MONTHLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 7, 1)),
                steps=4,
                first_week_size=2,
                level=StudyDownloadLevelDTO.MONTHLY,
            ),
        ),
        (
            {
                "first-month-in-year": "march",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 5,
                "simulation.end": 100,
            },
            StudyDownloadLevelDTO.HOURLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 3, 5)),
                steps=2304,
                first_week_size=1,
                level=StudyDownloadLevelDTO.HOURLY,
            ),
        ),
        (
            {
                "first-month-in-year": "march",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 5,
                "simulation.end": 100,
            },
            StudyDownloadLevelDTO.ANNUAL,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 3, 5)),
                steps=1,
                first_week_size=1,
                level=StudyDownloadLevelDTO.ANNUAL,
            ),
        ),
        (
            {
                "first-month-in-year": "march",
                "january.1st": "Sunday",
                "leapyear": False,
                "first.weekday": "Friday",
                "simulation.start": 3,
                "simulation.end": 100,
            },
            StudyDownloadLevelDTO.DAILY,
            MatrixIndex(
                start_date=str(datetime.datetime(2022, 3, 3)),
                steps=98,
                first_week_size=1,
                level=StudyDownloadLevelDTO.DAILY,
            ),
        ),
    ],
)
def test_create_matrix_index_output(config: Dict[str, Any], level: StudyDownloadLevelDTO, expected: MatrixIndex):
    config_mock = Mock()
    config_mock.archived = False
    output_id = "some output"

    file_study = Mock()
    file_study.tree.get.return_value = {"general": config}
    file_study.config.outputs = {output_id: config_mock}

    assert get_start_date(file_study, output_id, level) == expected


@pytest.mark.parametrize(
    "config,level,expected",
    [
        (
            {
                "first-month-in-year": "january",
                "january.1st": "Monday",
                "leapyear": True,
                "first.weekday": "Monday",
                "simulation.start": 1,
                "simulation.end": 354,
            },
            StudyDownloadLevelDTO.WEEKLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2024, 1, 1)),
                steps=53,
                first_week_size=7,
                level=StudyDownloadLevelDTO.WEEKLY,
            ),
        ),
        (
            {
                "first-month-in-year": "january",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 1,
                "simulation.end": 354,
            },
            StudyDownloadLevelDTO.WEEKLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2018, 1, 1)),
                steps=53,
                first_week_size=7,
                level=StudyDownloadLevelDTO.WEEKLY,
            ),
        ),
        (
            {
                "first-month-in-year": "july",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Wednesday",
                "simulation.start": 5,
                "simulation.end": 340,
            },
            StudyDownloadLevelDTO.WEEKLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 7, 1)),
                steps=53,
                first_week_size=4,
                level=StudyDownloadLevelDTO.WEEKLY,
            ),
        ),
        (
            {
                "first-month-in-year": "july",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 1,
                "simulation.end": 200,
            },
            StudyDownloadLevelDTO.MONTHLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 7, 1)),
                steps=12,
                first_week_size=2,
                level=StudyDownloadLevelDTO.MONTHLY,
            ),
        ),
        (
            {
                "first-month-in-year": "july",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 1,
                "simulation.end": 100,
            },
            StudyDownloadLevelDTO.MONTHLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 7, 1)),
                steps=12,
                first_week_size=2,
                level=StudyDownloadLevelDTO.MONTHLY,
            ),
        ),
        (
            {
                "first-month-in-year": "march",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 5,
                "simulation.end": 100,
            },
            StudyDownloadLevelDTO.HOURLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 3, 1)),
                steps=8760,
                first_week_size=5,
                level=StudyDownloadLevelDTO.HOURLY,
            ),
        ),
        (
            {
                "first-month-in-year": "march",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 5,
                "simulation.end": 100,
            },
            StudyDownloadLevelDTO.ANNUAL,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 3, 1)),
                steps=1,
                first_week_size=5,
                level=StudyDownloadLevelDTO.ANNUAL,
            ),
        ),
        (
            {
                "first-month-in-year": "march",
                "january.1st": "Sunday",
                "leapyear": False,
                "first.weekday": "Friday",
                "simulation.start": 3,
                "simulation.end": 100,
            },
            StudyDownloadLevelDTO.DAILY,
            MatrixIndex(
                start_date=str(datetime.datetime(2022, 3, 1)),
                steps=365,
                first_week_size=3,
                level=StudyDownloadLevelDTO.DAILY,
            ),
        ),
    ],
)
def test_create_matrix_index_input(config: Dict[str, Any], level: StudyDownloadLevelDTO, expected: MatrixIndex):
    file_study = Mock()
    file_study.tree.get.return_value = {"general": config}
    # Asserts the content are the same
    actual = get_start_date(file_study, None, level)
    assert actual == expected
    # Asserts the returned 1st January corresponds to the chosen one
    actual_datetime = datetime.datetime.strptime(actual.start_date, "%Y-%m-%d %H:%M:%S")
    next_year = str(actual_datetime.year + (actual_datetime.month != 1))
    first_january = datetime.datetime.strptime(next_year, "%Y").weekday()
    assert first_january == DAY_NAMES.index(config["january.1st"])
