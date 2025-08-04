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

from antarest.study.business.model.config.advanced_parameters_model import AdvancedParametersUpdate
from antarest.study.business.model.thematic_trimming_model import ThematicTrimmingUpdate
from antarest.study.model import (
    STUDY_VERSION_8,
    STUDY_VERSION_8_4,
    STUDY_VERSION_8_8,
    STUDY_VERSION_9_3,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_advanced_parameters import UpdateAdvancedParameters
from antarest.study.storage.variantstudy.model.command.update_thematic_trimming import UpdateThematicTrimming
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestUpdateThematicTrimming:
    def test_nominal_case(self, empty_study_880: FileStudy, command_context: CommandContext):
        study = empty_study_880
        general_data_content = study.tree.get(["settings", "generaldata"])

        args = {"power_fluctuations": "minimize ramping", "seed_tsgen_thermal": 33}
        parameters = AdvancedParametersUpdate.model_validate(args)

        command = UpdateAdvancedParameters(
            parameters=parameters, command_context=command_context, study_version=study.config.version
        )
        output = command.apply(study_data=study)
        assert output.status

        general_data_content["seeds - Mersenne Twister"]["seed-tsgen-thermal"] = 33
        general_data_content["other preferences"]["power-fluctuations"] = "minimize ramping"

        assert general_data_content == study.tree.get(["settings", "generaldata"])

    def test_error_cases(self, command_context: CommandContext):
        # Give fields that do not match the version
        parameters = ThematicTrimmingUpdate(res_generation_by_plant=True)
        with pytest.raises(
            ValidationError, match="Field res_generation_by_plant is not a valid field for study version 8"
        ):
            UpdateThematicTrimming(
                parameters=parameters, command_context=command_context, study_version=STUDY_VERSION_8
            )

        parameters = ThematicTrimmingUpdate(sts_lvl_by_plant=False)
        with pytest.raises(ValidationError, match="Field sts_lvl_by_plant is not a valid field for study version 8.4"):
            UpdateThematicTrimming(
                parameters=parameters, command_context=command_context, study_version=STUDY_VERSION_8_4
            )

        parameters = ThematicTrimmingUpdate(sts_by_group=True)
        with pytest.raises(
            ValidationError,
            match="Field sts_by_group is not a valid field for study version 8.8",
        ):
            UpdateThematicTrimming(
                parameters=parameters, command_context=command_context, study_version=STUDY_VERSION_8_8
            )

        parameters = ThematicTrimmingUpdate(nuclear=False)
        with pytest.raises(ValidationError, match="Field nuclear is not a valid field for study version 9.3"):
            UpdateThematicTrimming(
                parameters=parameters, command_context=command_context, study_version=STUDY_VERSION_9_3
            )
