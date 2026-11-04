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

import uuid
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from antares.study.version import StudyVersion

from antarest.core.exceptions import ChildNotFoundError
from antarest.study.storage.rawstudy.model.filesystem.config.model import AreaConfig, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix_storage_context import MatrixStorageContext
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.common.capacity import capacity

# noinspection SpellCheckingInspection
BEFORE_650: dict[str, dict[str, list[list[float]] | int | None]] = {
    "maxpower_en": {"default_empty": [[]], "nb_columns": None},
    "maxpower_fr": {"default_empty": [[]], "nb_columns": None},
    "reservoir_en": {"default_empty": [[]], "nb_columns": None},
    "reservoir_fr": {"default_empty": [[]], "nb_columns": None},
}

# noinspection SpellCheckingInspection
AFTER_650: dict[str, dict[str, list[list[float]] | int | None]] = {
    "creditmodulations_en": {"default_empty": [[]], "nb_columns": None},
    "creditmodulations_fr": {"default_empty": [[]], "nb_columns": None},
    "inflowPattern_en": {"default_empty": [[]], "nb_columns": None},
    "inflowPattern_fr": {"default_empty": [[]], "nb_columns": None},
    "maxpower_en": {"default_empty": [[]], "nb_columns": None},
    "maxpower_fr": {"default_empty": [[]], "nb_columns": None},
    "reservoir_en": {"default_empty": [[]], "nb_columns": None},
    "reservoir_fr": {"default_empty": [[]], "nb_columns": None},
    "waterValues_en": {"default_empty": [[]], "nb_columns": None},
    "waterValues_fr": {"default_empty": [[]], "nb_columns": None},
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
        expected: dict[str, Any],
    ) -> None:
        resolver = Mock(spec=MatrixStorageContext)
        context = resolver
        study_id = str(uuid.uuid4())
        config = FileStudyTreeConfig(
            study_path=Path("path/to/study"),
            path=Path("path/to/study"),
            study_id=study_id,
            version=StudyVersion.parse(version),
            areas={
                name: AreaConfig(
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
            matrix_storage_context=context,
            config=config,
            children_glob_exceptions=None,
        )
        actual = node.build()

        # check the result
        actual_obj: dict[str, dict[str, list[list[float]] | int | None]] = {}
        for key, value in actual.items():
            assert isinstance(value, InputSeriesMatrix)
            assert value.default_empty is not None
            actual_obj[key] = {"default_empty": [[]], "nb_columns": value.nb_columns}
        assert actual_obj == expected


@pytest.mark.parametrize(
    "version, optional",
    [
        ("9.1", False),
        ("9.2", True),
        ("10.2", True),
    ],
)
def test_missing_maxpower_only_allowed_since_v92(tmp_path: Path, version: str, optional: bool) -> None:
    capacity_path = tmp_path / "input/hydro/common/capacity"
    capacity_path.mkdir(parents=True)
    config = FileStudyTreeConfig(
        study_path=tmp_path,
        path=capacity_path,
        study_id="study",
        version=StudyVersion.parse(version),
        areas={
            "fr": AreaConfig(name="FR", links={}, thermals=[], renewables=[], filters_synthesis=[], filters_year=[])
        },
    )
    node = capacity.InputHydroCommonCapacity(Mock(spec=MatrixStorageContext), config).build()["maxpower_fr"]
    assert isinstance(node, InputSeriesMatrix)
    if optional:
        assert node.parse_content().is_empty()
        assert node.parse_as_dataframe().shape == (365, 4)
    else:
        with pytest.raises(ChildNotFoundError):
            node.parse_content()

    # Even in hourly mode, existing legacy values must be preserved.
    (capacity_path / "maxpower_fr.txt").write_text("1\t2\t3\t4\n")
    assert node.parse_content().rows() == [(1, 2, 3, 4)]
