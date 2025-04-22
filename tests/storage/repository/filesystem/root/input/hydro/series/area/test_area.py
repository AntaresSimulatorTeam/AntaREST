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

import uuid
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.matrixstore.uri_resolver_service import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import (
    default_scenario_daily,
    default_scenario_hourly,
    default_scenario_monthly,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.series.area import area

BEFORE_650 = {
    "mod": {
        "default_empty": default_scenario_monthly.tolist(),
        "freq": MatrixFrequency.MONTHLY,
        "nb_columns": None,
    },
    "ror": {
        "default_empty": default_scenario_hourly.tolist(),
        "freq": MatrixFrequency.HOURLY,
        "nb_columns": None,
    },
}

AFTER_650 = {
    "mod": {
        "default_empty": default_scenario_daily.tolist(),
        "freq": MatrixFrequency.DAILY,
        "nb_columns": None,
    },
    "ror": {
        "default_empty": default_scenario_hourly.tolist(),
        "freq": MatrixFrequency.HOURLY,
        "nb_columns": None,
    },
}

AFTER_860 = {
    "mod": {
        "default_empty": default_scenario_daily.tolist(),
        "freq": MatrixFrequency.DAILY,
        "nb_columns": None,
    },
    "ror": {
        "default_empty": default_scenario_hourly.tolist(),
        "freq": MatrixFrequency.HOURLY,
        "nb_columns": None,
    },
    "mingen": {
        "default_empty": default_scenario_hourly.tolist(),
        "freq": MatrixFrequency.HOURLY,
        "nb_columns": None,
    },
}


class TestInputHydroSeriesArea:
    @pytest.mark.parametrize(
        "version, expected",
        [
            pytest.param("000", BEFORE_650, id="before-650"),
            pytest.param("650", AFTER_650, id="after-650"),
            pytest.param("860", AFTER_860, id="after-860"),
        ],
    )
    def test_build_input_hydro_series_area(
        self,
        version: str,
        expected: dict,
    ):
        resolver = Mock(spec=MatrixUriMapper)
        context = resolver
        study_id = str(uuid.uuid4())
        config = FileStudyTreeConfig(
            study_path=Path("path/to/study"),
            path=Path("path/to/study"),
            study_id=study_id,
            version=int(version),  # will become a `str` in the future
            areas={},
        )

        node = area.InputHydroSeriesArea(
            matrix_mapper=context,
            config=config,
            children_glob_exceptions=None,
        )
        actual = node.build()

        # check the result
        actual_obj = {}
        for key, value in actual.items():
            assert isinstance(value, InputSeriesMatrix)
            actual_obj[key] = {
                "default_empty": value.default_empty.tolist(),
                "freq": value.freq,
                "nb_columns": value.nb_columns,
            }
        assert actual_obj == expected
