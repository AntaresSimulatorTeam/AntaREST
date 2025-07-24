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
from pydantic import ValidationError

from antarest.core.serde.ini_reader import read_ini
from antarest.study.business.model.hydro_model import HydroManagementUpdate
from antarest.study.model import STUDY_VERSION_9_2
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.update_hydro_management import UpdateHydroManagement
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestUpdateHydroManagement:
    def _set_up(self, study: FileStudy, command_context: CommandContext):
        CreateArea(area_name="FR", command_context=command_context, study_version=study.config.version).apply(study)
        CreateArea(area_name="be", command_context=command_context, study_version=study.config.version).apply(study)

    def test_lifecycle(self, empty_study_880: FileStudy, empty_study_920: FileStudy, command_context: CommandContext):
        for study in [empty_study_880, empty_study_920]:
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
            new_properties = HydroManagementUpdate.model_validate({"inter_daily_breakdown": 3.1, "reservoir": True})
            cmd = UpdateHydroManagement(
                area_id="fr", properties=new_properties, command_context=command_context, study_version=study_version
            )
            output = cmd.apply(study)
            assert output.status is True
            assert output.message == "Hydro properties in 'fr' updated."

            # Checks updated properties
            ini_content = read_ini(hydro_ini)
            expected_content = {
                "initialize reservoir date": {"be": 0, "fr": 0},
                "inter-daily-breakdown": {"be": 1.0, "fr": 3.1},  # the field has been updated
                "inter-monthly-breakdown": {"be": 1.0, "fr": 1.0},
                "intra-daily-modulation": {"be": 24.0, "fr": 24.0},
                "leeway low": {"be": 1.0, "fr": 1.0},
                "leeway up": {"be": 1.0, "fr": 1.0},
                "power to level": {"fr": False},
                "pumping efficiency": {"be": 1.0, "fr": 1.0},
                # Default fields are not present at the creation but are written by the command
                "reservoir": {"fr": True},  # the field has been written with the given value
                "reservoir capacity": {"fr": 0},
                "use heuristic": {"fr": True},
                "use leeway": {"fr": False},
                "use water": {"fr": False},
                "follow load": {"fr": True},
                "hard bounds": {"fr": False},
            }
            if study_version >= STUDY_VERSION_9_2:
                expected_content["overflow spilled cost difference"] = {"fr": 1.0}
            assert ini_content == expected_content

            # Update properties
            new_properties = HydroManagementUpdate.model_construct(overflow_spilled_cost_difference=1.4)
            if study_version < STUDY_VERSION_9_2:
                # Ensures we can't give a 9.2 parameter inside a v8.8 command
                with pytest.raises(
                    ValidationError,
                    match="Field overflow_spilled_cost_difference is not a valid field for study version 8.8",
                ):
                    UpdateHydroManagement(
                        area_id="fr",
                        properties=new_properties,
                        command_context=command_context,
                        study_version=study_version,
                    )
            else:
                cmd = UpdateHydroManagement(
                    area_id="fr",
                    properties=new_properties,
                    command_context=command_context,
                    study_version=study_version,
                )
                output = cmd.apply(study)
                assert output.status is True
                assert output.message == "Hydro properties in 'fr' updated."
                # Checks updated properties
                ini_content = read_ini(hydro_ini)
                expected_content["overflow spilled cost difference"] = {"fr": 1.4}
                assert ini_content == expected_content
