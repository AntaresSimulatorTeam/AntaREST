import pandas as pd

from pathlib import Path
from unittest.mock import Mock

from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.matrix.head_writer import (
    AreaHeadWriter,
)
from antarest.storage.repository.filesystem.matrix.output_series_matrix import (
    OutputSeriesMatrix,
)


def test_get(tmp_path: Path):
    file = tmp_path / "matrix-daily.txt"
    content = """
    DE	area	de	daily
    	VARIABLES	BEGIN	END
    	27	1	7

    DE	daily			01_solar	02_wind_on
    				MWh	MWh
    	index	day	month	EXP	EXP
    	1	01	JAN	27000	600
    	2	02	JAN	48000	34400
        """
    file.write_text(content)
    config = StudyConfig(study_path=file)

    serializer = Mock()
    serializer.extract_date.return_value = (
        pd.DatetimeIndex(pd.to_datetime(["2020/01/01", "2020/01/02"])),
        pd.DataFrame(
            data={
                "01_solar": ["MWh", "EXP", "27000", "48000"],
                "02_wind_on": ["MWh", "EXP", "600", "34400"],
            }
        ),
    )

    matrix = pd.DataFrame(
        data={
            "01_solar::MWh::EXP": [27000, 48000],
            "02_wind_on::MWh::EXP": [600, 34400],
        },
        index=pd.to_datetime(["2020/01/01", "2020/01/02"]),
    )

    node = OutputSeriesMatrix(config, serializer, AreaHeadWriter("", ""))
    assert node.get() == matrix.to_dict()


def test_save(tmp_path: Path):
    file = tmp_path / "matrix-daily.txt"
    config = StudyConfig(study_path=file)

    serializer = Mock()
    serializer.build_date.return_value = pd.DataFrame(
        {
            0: ["DE", "", "", "", ""],
            1: ["hourly", "", "index", 1, 2],
            2: ["", "", "day", "1", "1"],
            3: ["", "", "month", "JAN", "JAN"],
            4: ["", "", "hourly", "00:00", "01:00"],
        }
    )

    node = OutputSeriesMatrix(
        config, serializer, AreaHeadWriter(area="de", freq="hourly")
    )

    matrix = pd.DataFrame(
        data={
            "01_solar::MWh::EXP": [27000, 48000],
            "02_wind_on::MWh::EXP": [600, 34400],
        },
        index=pd.to_datetime(["2020/01/01", "2020/01/02"]),
    )

    node.save(matrix.to_dict())
    print(file.read_text())
    assert (
        file.read_text()
        == """DE	area	de	hourly
	VARIABLES	BEGIN	END
	2	1	2

DE	hourly				01_solar	02_wind_on
					MWh	MWh
	index	day	month	hourly	EXP	EXP
	1	1	JAN	00:00	27000	600
	2	1	JAN	01:00	48000	34400
"""
    )
