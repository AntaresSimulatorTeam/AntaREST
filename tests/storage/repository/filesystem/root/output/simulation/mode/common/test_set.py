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

import typing as t
import uuid
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import AreaOutputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common import set


class TestOutputSimulationSet:
    @pytest.mark.parametrize(
        "existing_files",
        [
            pytest.param(["id-hourly.txt", "values-annual.txt"]),
            pytest.param([]),
        ],
    )
    def test_output_simulation_set(self, existing_files: t.List[str], tmp_path: Path):
        expected = {}
        for file in existing_files:
            tmp_path.joinpath(file).touch()
            name = Path(file).stem
            expected[name] = {"freq": MatrixFrequency(name.split("-")[1])}
        resolver = Mock(spec=UriResolverService)
        study_id = str(uuid.uuid4())
        config = FileStudyTreeConfig(
            study_path=Path("study_path"),
            path=tmp_path,
            study_id=study_id,
            version=850,  # will become a `str` in the future
            areas={},
        )

        node = set.OutputSimulationSet(context=resolver, config=config, set="foo")
        actual = node.build()

        # check the result
        actual_obj: dict[str, dict[str, MatrixFrequency]] = {}
        for key, value in actual.items():
            assert isinstance(value, AreaOutputSeriesMatrix)
            actual_obj[key] = {"freq": value.freq}
        assert actual_obj == expected
