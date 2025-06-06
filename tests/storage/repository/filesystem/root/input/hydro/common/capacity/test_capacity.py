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

from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.common.capacity import capacity

# noinspection SpellCheckingInspection
BEFORE_650 = {
    "maxpower_en": {"default_empty": [[]], "freq": MatrixFrequency.DAILY, "nb_columns": None},
    "maxpower_fr": {"default_empty": [[]], "freq": MatrixFrequency.DAILY, "nb_columns": None},
    "reservoir_en": {"default_empty": [[]], "freq": MatrixFrequency.DAILY, "nb_columns": None},
    "reservoir_fr": {"default_empty": [[]], "freq": MatrixFrequency.DAILY, "nb_columns": None},
}

# noinspection SpellCheckingInspection
AFTER_650 = {
    "creditmodulations_en": {"default_empty": [[]], "freq": MatrixFrequency.HOURLY, "nb_columns": None},
    "creditmodulations_fr": {"default_empty": [[]], "freq": MatrixFrequency.HOURLY, "nb_columns": None},
    "inflowPattern_en": {"default_empty": [[]], "freq": MatrixFrequency.DAILY, "nb_columns": None},
    "inflowPattern_fr": {"default_empty": [[]], "freq": MatrixFrequency.DAILY, "nb_columns": None},
    "maxpower_en": {"default_empty": [[]], "freq": MatrixFrequency.DAILY, "nb_columns": None},
    "maxpower_fr": {"default_empty": [[]], "freq": MatrixFrequency.DAILY, "nb_columns": None},
    "reservoir_en": {"default_empty": [[]], "freq": MatrixFrequency.DAILY, "nb_columns": None},
    "reservoir_fr": {"default_empty": [[]], "freq": MatrixFrequency.DAILY, "nb_columns": None},
    "waterValues_en": {"default_empty": [[]], "freq": MatrixFrequency.DAILY, "nb_columns": None},
    "waterValues_fr": {"default_empty": [[]], "freq": MatrixFrequency.DAILY, "nb_columns": None},
}


class TestInputHydroCommonCapacity:
    @pytest.mark.parametrize(
        "version, expected",
        [
            pytest.param("000", BEFORE_650, id="before-650"),
            pytest.param("650", AFTER_650, id="after-650"),
        ],
    )
    def test_build_input_hydro_common_capacity(
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
            areas={
                name: Area(
                    name=name.upper(),
                    links={},
                    thermals=[],
                    renewables=[],
                    filters_synthesis=[],
                    filters_year=[],
                )
                for name in ["fr", "en"]
            },
        )

        node = capacity.InputHydroCommonCapacity(
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
                "default_empty": [[]],
                "freq": value.freq,
                "nb_columns": value.nb_columns,
            }
        assert actual_obj == expected
