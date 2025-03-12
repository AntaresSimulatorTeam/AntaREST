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

from antarest.study.business.model.xpansion_model import XpansionSettingsUpdate
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_xpansion_settings import UpdateXpansionSettings
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestUpdateXpansionSettings:
    @staticmethod
    def set_up(empty_study: FileStudy):
        empty_study.tree.save(
            {
                "user": {
                    "expansion": {
                        "capa": {},
                        "weights": {},
                        "constraints": {},
                        "settings": {
                            "master": "integer",
                            "uc_type": "expansion_fast",
                            "optimality_gap": 1,
                            "relative_gap": 0.000001,
                            "relaxed_optimality_gap": 0.00001,
                            "max_iteration": 1000,
                            "solver": "Xpress",
                            "log_level": 0,
                            "separation_parameter": 0.5,
                            "batch_size": 96,
                            "timelimit": 1000000000000,
                        },
                        "candidates": {},
                    }
                }
            }
        )
        study_path = empty_study.config.study_path
        xpansion_path = study_path / "user" / "expansion"
        (xpansion_path / "capa" / "capa1.txt").touch()
        (xpansion_path / "weights" / "weights1.txt").touch()

    @pytest.mark.parametrize("empty_study", ["empty_study_870.zip"], indirect=True)
    def test_nominal_case(self, empty_study: FileStudy, command_context: CommandContext):
        self.set_up(empty_study)

        # Add yearly_weights
        new_constraint = XpansionSettingsUpdate.model_validate({"yearly_weights": "weights1.txt"})
        cmd = UpdateXpansionSettings(
            settings=new_constraint,
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        )
        output = cmd.apply(study_data=empty_study)
        assert output.status, output.message
        # Checks DTO
        assert cmd.to_dto().args == {"settings": {"yearly-weights": "weights1.txt"}}
        # Checks ini content
        settings_path = empty_study.config.study_path / "user" / "expansion" / "settings.ini"
        assert "yearly-weights=weights1.txt" in settings_path.read_text()

        # Basic update to also remove the yearly_weight
        new_settings = XpansionSettingsUpdate.model_validate({"optimality_gap": 12})
        cmd = UpdateXpansionSettings(
            settings=new_settings,
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        )
        output = cmd.apply(study_data=empty_study)
        assert output.status, output.message
        # Checks DTO
        assert cmd.to_dto().args == {"settings": {"optimality_gap": 12.0}}
        # Checks ini content
        assert "optimality_gap=12.0" in settings_path.read_text()
        assert "yearly-weights" not in settings_path.read_text()

    @pytest.mark.parametrize("empty_study", ["empty_study_870.zip"], indirect=True)
    def test_error_cases(self, empty_study: FileStudy, command_context: CommandContext):
        self.set_up(empty_study)

        # Try to update with a non-existing weight
        new_constraint = XpansionSettingsUpdate.model_validate({"yearly_weights": "test"})
        cmd = UpdateXpansionSettings(
            settings=new_constraint,
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        )
        output = cmd.apply(study_data=empty_study)
        assert output.status is False
        assert "Additional weights file 'test' does not exist" in output.message

        # Try to update with a non-existing constraint
        new_constraint = XpansionSettingsUpdate.model_validate({"additional_constraints": "test"})
        cmd = UpdateXpansionSettings(
            settings=new_constraint,
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        )
        output = cmd.apply(study_data=empty_study)
        assert output.status is False
        assert "Additional constraints file 'test' does not exist" in output.message
