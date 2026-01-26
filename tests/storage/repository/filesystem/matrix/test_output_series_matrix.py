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

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from antarest.core.exceptions import ChildNotFoundError, MustNotModifyOutputException
from antarest.study.model import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
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

    def test_parse_dataframe(self, my_study_config: FileStudyTreeConfig) -> None:
        # The content corresponds to a real `values-annual.txt` file.
        content = b"AT\tarea\tva\tannual\n\tVARIABLES\tBEGIN\tEND\n\t9\t1\t1\n\nAT\tannual\tOV. COST\tMRG. PRICE\tBattery_injection\tBattery_withdrawal\tBattery_level\tUNSP. ENRG\tSPIL. ENRG\tLOLD\tLOLP\n\t\tEuro\tEuro\tMW\tMW\tMWh\tMWh\tMWh\tHours\t%\n\t\t\t\t\t\t\t\t\t\t\n\tAnnual\t3573604931\t87.1175\t0\t0\t0\t0\t0\t0\t100.00\n"
        my_study_config.path.write_bytes(content)

        data = np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 100.0]])
        columns = pd.Index(
            [
                ("Battery_injection", "MW", ""),
                ("Battery_withdrawal", "MW", ""),
                ("Battery_level", "MWh", ""),
                ("UNSP. ENRG", "MWh", ""),
                ("SPIL. ENRG", "MWh", ""),
                ("LOLD", "Hours", ""),
                ("LOLP", "%", ""),
            ],
        )
        expected_result = pd.DataFrame(data, columns=columns)

        node = OutputSeriesMatrix(config=my_study_config, freq=MatrixFrequency.DAILY)
        pd.testing.assert_frame_equal(node.parse_dataframe(), expected_result, check_dtype=False)

    def test_parse_dataframe_file_not_found(self, my_study_config: FileStudyTreeConfig) -> None:
        node = OutputSeriesMatrix(config=my_study_config, freq=MatrixFrequency.DAILY)
        with pytest.raises(ChildNotFoundError) as ctx:
            node.parse_dataframe()
        err_msg = str(ctx.value)
        assert "'matrix-daily.txt" in err_msg
        assert my_study_config.study_id in err_msg
        assert "not found" in err_msg.lower()

    def test_save(self, my_study_config: FileStudyTreeConfig) -> None:
        node = OutputSeriesMatrix(config=my_study_config, freq=MatrixFrequency.DAILY)

        with pytest.raises(MustNotModifyOutputException, match="Should not modify output file"):
            node.dump(data={})
