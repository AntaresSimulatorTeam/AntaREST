import datetime
import tarfile
from hashlib import md5
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock
from zipfile import ZipFile

import pytest

from antarest.study.model import (
    MatrixAggregationResult,
    MatrixIndex,
    StudyDownloadLevelDTO,
    ExportFormat,
    TimeSeriesData,
    StudyDownloadType,
    TimeSerie,
    MatrixAggregationResultDTO,
)
from antarest.study.storage.study_download_utils import StudyDownloader
from antarest.study.storage.utils import get_start_date


def test_output_downloads_export(tmp_path: Path):
    matrix = MatrixAggregationResultDTO(
        index=MatrixIndex(start_date="2000-01-01 00:00:00"),
        data=[
            TimeSeriesData(
                name="a1",
                type=StudyDownloadType.AREA,
                data={
                    "1": [
                        TimeSerie(name="A", unit="", data=[1, 2, 3, 4]),
                        TimeSerie(name="B", unit="", data=[5, 6, 7, 8]),
                    ],
                    "2": [
                        TimeSerie(name="A", unit="", data=[10, 11, 12, 13]),
                        TimeSerie(
                            name="B", unit="", data=[14, None, None, 15]
                        ),
                    ],
                },
            ),
            TimeSeriesData(
                name="a2",
                type=StudyDownloadType.AREA,
                data={
                    "1": [
                        TimeSerie(name="A", unit="", data=[16, 17, 18, 19]),
                        TimeSerie(name="B", unit="", data=[20, 21, 22, 23]),
                    ],
                    "2": [
                        TimeSerie(name="A", unit="", data=[24, None, 25, 26]),
                        TimeSerie(name="B", unit="", data=[27, 28, 29, 30]),
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
        assert (
            md5(zip_input.read("a1.csv")).hexdigest()
            == "e183e79f2184d6f6dacb8ad215cb056c"
        )
        assert (
            md5(zip_input.read("a2.csv")).hexdigest()
            == "c007db83f2769e6128e0f8c6b04d43eb"
        )

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
                steps=50,
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
                start_date=str(datetime.datetime(2001, 1, 1)),
                steps=50,
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
                start_date=str(datetime.datetime(2002, 7, 5)),
                steps=47,
                first_week_size=5,
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
                start_date=str(datetime.datetime(2002, 7, 1)),
                steps=7,
                first_week_size=7,
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
                start_date=str(datetime.datetime(2002, 7, 1)),
                steps=4,
                first_week_size=7,
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
                start_date=str(datetime.datetime(2010, 3, 5)),
                steps=2184,
                first_week_size=3,
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
                start_date=str(datetime.datetime(2010, 3, 5)),
                steps=1,
                first_week_size=3,
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
                start_date=str(datetime.datetime(2009, 3, 3)),
                steps=91,
                first_week_size=3,
                level=StudyDownloadLevelDTO.DAILY,
            ),
        ),
    ],
)
def test_create_matrix_index(
    config: Dict[str, Any], level: StudyDownloadLevelDTO, expected: MatrixIndex
):
    file_study = Mock()
    file_study.tree.get.return_value = {"general": config}
    assert get_start_date(file_study, "some output", level) == expected
