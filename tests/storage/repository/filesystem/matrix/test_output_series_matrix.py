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

from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

from antarest.core.exceptions import ChildNotFoundError, MustNotModifyOutputException
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.matrix.head_writer import AreaHeadWriter
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import OutputSeriesMatrix

MATRIX_DAILY_DATA = """\
DE\tarea\tva\thourly
\tVARIABLES\tBEGIN\tEND
\t2\t1\t2

DE\thourly\t\t\t\t01_solar\t02_wind_on
\t\t\t\t\tMWh\tMWh
\tindex\tday\tmonth\thourly\tEXP\tEXP
\t1\t1\tJAN\t00:00\t27000\t600
\t2\t1\tJAN\t01:00\t48000\t34400
"""


class TestOutputSeriesMatrix:
    @pytest.fixture(name="my_study_config")
    def fixture_my_study_config(self, tmp_path: Path) -> FileStudyTreeConfig:
        """
        Construct a FileStudyTreeConfig object for a dummy study stored in a temporary directory.
        """
        return FileStudyTreeConfig(
            study_path=tmp_path,
            path=tmp_path / "matrix-daily.txt",
            study_id="df0a8aa9-6c6f-4e8b-a84e-45de2fb29cd3",
            version=800,
        )

    def test_load(self, my_study_config: FileStudyTreeConfig) -> None:
        file = my_study_config.path
        file.write_text("\n\n\n\nmock\tfile\ndummy\tdummy\ndummy\tdummy\ndummy\tdummy")

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
            matrix_mapper=Mock(),
            config=my_study_config,
            freq=MatrixFrequency.DAILY,
            date_serializer=serializer,
            head_writer=AreaHeadWriter(area="", data_type="", freq=""),
        )
        assert node.load() == matrix.to_dict(orient="split")

    def test_load__file_not_found(self, my_study_config: FileStudyTreeConfig) -> None:
        node = OutputSeriesMatrix(
            matrix_mapper=Mock(),
            config=my_study_config,
            freq=MatrixFrequency.DAILY,
            date_serializer=Mock(),
            head_writer=AreaHeadWriter(area="", data_type="", freq=""),
        )
        with pytest.raises(ChildNotFoundError) as ctx:
            node.load()
        err_msg = str(ctx.value)
        assert "'matrix-daily.txt" in err_msg
        assert my_study_config.study_id in err_msg
        assert "not found" in err_msg.lower()

    def test_save(self, my_study_config: FileStudyTreeConfig) -> None:
        node = OutputSeriesMatrix(
            matrix_mapper=Mock(),
            config=my_study_config,
            freq=MatrixFrequency.DAILY,
            date_serializer=Mock(),
            head_writer=AreaHeadWriter(area="de", data_type="va", freq="hourly"),
        )

        with pytest.raises(MustNotModifyOutputException, match="Should not modify output file"):
            node.dump(data={})
