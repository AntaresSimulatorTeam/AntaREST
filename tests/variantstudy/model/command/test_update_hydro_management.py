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
from study.business.model.hydro_model import HydroManagementUpdate
from study.storage.rawstudy.model.filesystem.factory import FileStudy
from study.storage.variantstudy.model.command.create_area import CreateArea
from study.storage.variantstudy.model.command.update_hydro_management import UpdateHydroManagement
from study.storage.variantstudy.model.command_context import CommandContext

from antarest.core.serde.ini_reader import read_ini


class TestUpdateHydroManagement:
    def _set_up(self, study: FileStudy, command_context: CommandContext):
        CreateArea(area_name="FR", command_context=command_context, study_version=study.config.version).apply(study)
        CreateArea(area_name="be", command_context=command_context, study_version=study.config.version).apply(study)

    def test_version_880(self, empty_study_880: FileStudy, command_context: CommandContext):
        study = empty_study_880
        study_version = study.config.version
        self._set_up(study, command_context)
        # study_version = empty_study.config.version
        study_path = study.config.study_path

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

        # Update several properties
        new_properties = HydroManagementUpdate(**{"inter_daily_breakdown": 3.1, "reservoir": True})
        # new_properties = {"inter_daily_breakdown": 3.1, "reservoir": True}
        cmd = UpdateHydroManagement(area_id="fr",properties=new_properties, command_context=command_context, study_version=study_version)
        cmd.apply(study)