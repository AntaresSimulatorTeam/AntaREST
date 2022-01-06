import datetime
from hashlib import md5
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock
from zipfile import ZipFile

import pytest

from antarest.core.model import JSON
from antarest.study.model import (
    MatrixAggregationResult,
    MatrixIndex,
    StudyDownloadLevelDTO,
)
from antarest.study.storage.study_download_utils import StudyDownloader


def test_output_downloads_export(tmp_path: Path):
    matrix = MatrixAggregationResult(
        index=MatrixIndex(),
        data={
            "a1": {
                "1": {
                    "A": [1, 2, 3, 4],
                    "B": [5, 6, 7, 8],
                },
                "2": {
                    "A": [10, 11, 12, 13],
                    "B": [14, None, None, 15],
                },
            },
            "a2": {
                "1": {
                    "A": [16, 17, 18, 19],
                    "B": [20, 21, 22, 23],
                },
                "2": {
                    "A": [24, None, 25, 26],
                    "B": [27, 28, 29, 30],
                },
            },
        },
        warnings=[],
    )
    zip_file = tmp_path / "output.zip"
    StudyDownloader.export(matrix, "application/zip", zip_file)
    with ZipFile(zip_file) as zip_input:
        assert zip_input.namelist() == ["a1.csv", "a2.csv"]
        assert (
            md5(zip_input.read("a1.csv")).hexdigest()
            == "eec20effc24b12284991f039f146fc9b"
        )
        assert (
            md5(zip_input.read("a2.csv")).hexdigest()
            == "f914fc39e32c3d02f491fed302513961"
        )


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
                start_date=str(datetime.datetime(2001, 1, 1)),
                steps=51,
                first_week_size=7,
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
                start_date=str(datetime.datetime(2002, 7, 5)),
                steps=48,
                first_week_size=5,
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
                start_date=str(datetime.datetime(2002, 7, 1)),
                steps=7,
                first_week_size=7,
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
                start_date=str(datetime.datetime(2002, 7, 1)),
                steps=4,
                first_week_size=7,
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
                start_date=str(datetime.datetime(2010, 3, 5)),
                steps=2280,
                first_week_size=3,
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
                start_date=str(datetime.datetime(2010, 3, 5)),
                steps=1,
                first_week_size=3,
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
                start_date=str(datetime.datetime(2009, 3, 3)),
                steps=97,
                first_week_size=3,
            ),
        ),
    ],
)
def test_create_matrix_index(
    config: Dict[str, Any], level: StudyDownloadLevelDTO, expected: MatrixIndex
):
    file_study = Mock()
    file_study.tree.get.return_value = config
    assert (
        StudyDownloader.get_start_date(file_study, "some output", level)
        == expected
    )
