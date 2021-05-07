import pandas as pd

from pathlib import Path
from unittest.mock import Mock

from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.matrix.output_series_matrix import (
    OutputSeriesMatrix,
)


def test(tmp_path: Path):
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

    node = OutputSeriesMatrix(config, serializer)
    assert node.get() == matrix.to_dict()
