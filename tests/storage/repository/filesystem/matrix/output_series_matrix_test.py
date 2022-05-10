from pathlib import Path
from unittest.mock import Mock

import pandas as pd

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.head_writer import (
    AreaHeadWriter,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    OutputSeriesMatrix,
)


def test_get(tmp_path: Path):
    file = tmp_path / "matrix-daily.txt"
    file.write_text(
        "\n\n\n\nmock\tfile\ndummy\tdummy\ndummy\tdummy\ndummy\tdummy"
    )
    config = FileStudyTreeConfig(
        study_path=file, path=file, study_id="id", version=-1
    )

    serializer = Mock()
    serializer.extract_date.return_value = (
        pd.Index(["01/02", "01/01"]),
        pd.DataFrame(
            data={
                ("01_solar", "MWh", "EXP"): [27000, 48000],
                ("02_wind_on", "MWh", "EXP"): [600, 34400],
            }
        ),
    )

    matrix = pd.DataFrame(
        data={
            ("01_solar", "MWh", "EXP"): [27000, 48000],
            ("02_wind_on", "MWh", "EXP"): [600, 34400],
        },
        index=["01/02", "01/01"],
    )

    node = OutputSeriesMatrix(
        context=Mock(),
        config=config,
        date_serializer=serializer,
        head_writer=AreaHeadWriter(area="", data_type="", freq=""),
        freq="",
    )
    assert node.load() == matrix.to_dict(orient="split")


def test_save(tmp_path: Path):
    file = tmp_path / "matrix-daily.txt"
    config = FileStudyTreeConfig(
        study_path=file, path=file, study_id="id", version=-1
    )

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
        context=Mock(),
        config=config,
        date_serializer=serializer,
        head_writer=AreaHeadWriter(area="de", data_type="va", freq="hourly"),
        freq="",
    )

    matrix = pd.DataFrame(
        data={
            ("01_solar", "MWh", "EXP"): [27000, 48000],
            ("02_wind_on", "MWh", "EXP"): [600, 34400],
        },
        index=["01/01", "01/02"],
    )

    node.dump(matrix.to_dict(orient="split"))
    print(file.read_text())
    assert (
        file.read_text()
        == """DE	area	va	hourly
	VARIABLES	BEGIN	END
	2	1	2

DE	hourly				01_solar	02_wind_on
					MWh	MWh
	index	day	month	hourly	EXP	EXP
	1	1	JAN	00:00	27000	600
	2	1	JAN	01:00	48000	34400
"""
    )
