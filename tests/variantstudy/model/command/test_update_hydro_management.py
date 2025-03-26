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
import pytest
from study.storage.rawstudy.model.filesystem.factory import FileStudy
from study.storage.variantstudy.model.command.create_area import CreateArea
from study.storage.variantstudy.model.command_context import CommandContext

from antarest.core.serde.ini_reader import read_ini


class TestUpdateHydroManagement:
    def _set_up(self, study: FileStudy, command_context: CommandContext):
        CreateArea(area_name="FR", command_context=command_context, study_version=study.config.version).apply(study)
        CreateArea(area_name="be", command_context=command_context, study_version=study.config.version).apply(study)

    @pytest.mark.parametrize("empty_study", ["empty_study_870.zip"], indirect=True)
    def test_nominal_case(self, empty_study: FileStudy, command_context: CommandContext):
        self._set_up(empty_study, command_context)
        # study_version = empty_study.config.version
        study_path = empty_study.config.study_path

        # Check existing file
        hydro_ini = study_path / "input" / "hydro" / "hydro.ini"
        ini_content = read_ini(hydro_ini)
        assert ini_content == {
            "inter-daily-breakdown": {"fr": 1, "be": 1},
            "intra-daily-modulation": {"fr": 24, "be": 24},
            "inter-monthly-breakdown": {"fr": 1, "be": 1},
            "initialize reservoir date": {"fr": 0, "be": 0},
            "leeway low": {"fr": 1, "be": 1},
            "leeway up": {"fr": 1, "be": 1},
            "pumping efficiency": {"fr": 1, "be": 1},
        }
