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
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    BindingConstraintOutputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common import binding_const


class TestOutputSimulationBindingConstraintItem:
    @pytest.mark.parametrize(
        "existing_files",
        [
            pytest.param(["binding-constraints-hourly.txt", "binding-constraints-daily.txt"]),
            pytest.param([]),
        ],
    )
    def test_build_output_simulation_binding_constraint_item(self, existing_files: t.List[str], tmp_path: Path):
        expected = {}
        for file in existing_files:
            tmp_path.joinpath(file).touch()
            name = Path(file).stem
            expected[name] = {"freq": MatrixFrequency(name.replace("binding-constraints-", ""))}
        resolver = Mock(spec=UriResolverService)
        context = ContextServer(resolver=resolver)
        study_id = str(uuid.uuid4())
        config = FileStudyTreeConfig(
            study_path=Path("path/to/study"),
            path=tmp_path,
            study_id=study_id,
            version=850,  # will become a `str` in the future
            areas={},
        )

        node = binding_const.OutputSimulationBindingConstraintItem(context=context, config=config)
        actual = node.build()

        # check the result
        actual_obj: dict[str, dict[str, MatrixFrequency]] = {}
        for key, value in actual.items():
            assert isinstance(value, BindingConstraintOutputSeriesMatrix)
            actual_obj[key] = {"freq": value.freq}
        assert actual_obj == expected
