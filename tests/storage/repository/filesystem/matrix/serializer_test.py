from pathlib import Path

import pandas as pd

from antarest.storage.repository.filesystem.matrix.date_serializer import (
    DailyMatrixSerializer,
    MonthlyMatrixSerializer,
)


def test_daily(tmp_path: Path):
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

    df = pd.read_csv(file, sep="\t", skiprows=4)

    serializer = DailyMatrixSerializer()
    date, body = serializer.extract_date(df)

    pd.testing.assert_index_equal(
        date, pd.DatetimeIndex(pd.to_datetime(["2020/01/01", "2020/01/02"]))
    )

    pd.testing.assert_frame_equal(
        body,
        pd.DataFrame(
            data={
                "01_solar": ["MWh", "EXP", "27000", "48000"],
                "02_wind_on": ["MWh", "EXP", "600", "34400"],
            }
        ),
    )


def test_monthly(tmp_path: Path):
    file = tmp_path / "matrix-monthly.txt"
    content = """
DE	area	de	monthly
	VARIABLES	BEGIN	END
	27	1	1

DE	monthly		01_solar	02_wind_on
			MWh	MWh
	index	month	EXP	EXP
	1	JAN	315000	275000
    """
    file.write_text(content)

    df = pd.read_csv(file, sep="\t", skiprows=4)

    serializer = MonthlyMatrixSerializer()
    date, body = serializer.extract_date(df)

    pd.testing.assert_index_equal(
        date, pd.DatetimeIndex(pd.to_datetime(["2020/01/01"]))
    )

    pd.testing.assert_frame_equal(
        body,
        pd.DataFrame(
            data={
                "01_solar": ["MWh", "EXP", "315000"],
                "02_wind_on": ["MWh", "EXP", "275000"],
            }
        ),
    )
