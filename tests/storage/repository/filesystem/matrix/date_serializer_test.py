from pathlib import Path

import pandas as pd

from antarest.storage.repository.filesystem.matrix.date_serializer import (
    DailyMatrixSerializer,
    MonthlyMatrixSerializer,
    HourlyMatrixSerializer,
    WeeklyMatrixSerializer,
    AnnualMatrixSerializer,
)


def test_extract_hourly(tmp_path: Path):
    file = tmp_path / "matrix-daily.txt"
    content = """
DE	hourly				01_solar	02_wind_on
					MWh	MWh
	index	day	month	hour		
	1	1	JAN	00:00	0	0
	2	1	JAN	01:00	100	0
    """
    file.write_text(content)

    df = pd.read_csv(file, sep="\t")
    df.fillna("", inplace=True)

    serializer = HourlyMatrixSerializer()
    date, body = serializer.extract_date(df)

    pd.testing.assert_index_equal(date, pd.Index(["00:00 1/01", "01:00 1/01"]))

    pd.testing.assert_frame_equal(
        body,
        pd.DataFrame(
            data={
                "01_solar": ["MWh", "", "0", "100"],
                "02_wind_on": ["MWh", "", "0", "0"],
            }
        ),
    )


def test_build_hourly(tmp_path: Path):
    exp = pd.DataFrame(
        {
            0: ["DE", "", "", "", ""],
            1: ["hourly", "", "index", 1, 2],
            2: ["", "", "day", "1", "1"],
            3: ["", "", "month", "JAN", "JAN"],
            4: ["", "", "hourly", "00:00", "01:00"],
        }
    )

    index = pd.Index(["00:00 1/01", "01:00 1/01"])

    serializer = HourlyMatrixSerializer(area="de")
    res = serializer.build_date(index)
    assert exp.values.tolist() == res.values.tolist()


def test_daily(tmp_path: Path):
    file = tmp_path / "matrix-daily.txt"
    content = """
DE	daily			01_solar	02_wind_on
				MWh	MWh
	index	day	month	EXP	EXP
	1	01	JAN	27000	600
	2	02	JAN	48000	34400
    """
    file.write_text(content)

    df = pd.read_csv(file, sep="\t")

    serializer = DailyMatrixSerializer()
    date, body = serializer.extract_date(df)

    pd.testing.assert_index_equal(date, pd.Index(["01/01", "02/01"]))

    pd.testing.assert_frame_equal(
        body,
        pd.DataFrame(
            data={
                "01_solar": ["MWh", "EXP", "27000", "48000"],
                "02_wind_on": ["MWh", "EXP", "600", "34400"],
            }
        ),
    )


def test_weekly(tmp_path: Path):
    file = tmp_path / "matrix-daily.txt"
    content = """
DE	weekly	01_solar	02_wind_on
		MWh	MWh
	week		
	1	315000	275000
    """
    file.write_text(content)

    df = pd.read_csv(file, sep="\t")
    df.fillna("", inplace=True)

    serializer = WeeklyMatrixSerializer()
    date, body = serializer.extract_date(df)

    pd.testing.assert_index_equal(date, pd.Index(range(1)))

    pd.testing.assert_frame_equal(
        body,
        pd.DataFrame(
            data={
                "01_solar": ["MWh", "", "315000"],
                "02_wind_on": ["MWh", "", "275000"],
            }
        ),
    )


def test_monthly(tmp_path: Path):
    file = tmp_path / "matrix-monthly.txt"
    content = """
DE	monthly		01_solar	02_wind_on
			MWh	MWh
	index	month	EXP	EXP
	1	JAN	315000	275000
    """
    file.write_text(content)

    df = pd.read_csv(file, sep="\t")

    serializer = MonthlyMatrixSerializer()
    date, body = serializer.extract_date(df)

    pd.testing.assert_index_equal(date, pd.Index(["01"], name="month"))

    pd.testing.assert_frame_equal(
        body,
        pd.DataFrame(
            data={
                "01_solar": ["MWh", "EXP", "315000"],
                "02_wind_on": ["MWh", "EXP", "275000"],
            }
        ),
    )


def test_annual(tmp_path: Path):
    file = tmp_path / "matrix-daily.txt"
    content = """
DE	annual	01_solar	02_wind_on
		MWh	MWh
			
	Annual	315000	275000
    """
    file.write_text(content)

    df = pd.read_csv(file, sep="\t")
    df.fillna("", inplace=True)

    serializer = AnnualMatrixSerializer()
    date, body = serializer.extract_date(df)

    pd.testing.assert_index_equal(date, pd.Index(["Annual"], name="annual"))

    pd.testing.assert_frame_equal(
        body,
        pd.DataFrame(
            data={
                "01_solar": ["MWh", "", "315000"],
                "02_wind_on": ["MWh", "", "275000"],
            }
        ),
    )
