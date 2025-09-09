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
from antarest.study.model import STUDY_VERSION_8_7, STUDY_VERSION_9_2
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_advanced_parameters import UpdateAdvancedParameters
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestUpdateAdvancedParameters:
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
        parameters = AdvancedParametersUpdate(**{"unit_commitment_mode": "milp"})
        with pytest.raises(ValidationError, match="Unit commitment mode `MILP` only exists in v8.8+"):
            UpdateAdvancedParameters(
                parameters=parameters, command_context=command_context, study_version=STUDY_VERSION_8_7
            )

        parameters = AdvancedParametersUpdate(**{"shedding_policy": "accurate shave peaks"})
        with pytest.raises(ValidationError, match="Shedding policy `accurate shave peaks` only exists in v9.2+"):
            UpdateAdvancedParameters(
                parameters=parameters, command_context=command_context, study_version=STUDY_VERSION_8_7
            )

        parameters = AdvancedParametersUpdate(**{"accurate_shave_peaks_include_short_term_storage": False})
        with pytest.raises(
            ValidationError,
            match="Field accurate_shave_peaks_include_short_term_storage is not a valid field for study version 8.7",
        ):
            UpdateAdvancedParameters(
                parameters=parameters, command_context=command_context, study_version=STUDY_VERSION_8_7
            )

        parameters = AdvancedParametersUpdate(**{"initial_reservoir_levels": "cold start"})
        with pytest.raises(
            ValidationError, match="Field initial_reservoir_levels is not a valid field for study version 9.2"
        ):
            UpdateAdvancedParameters(
                parameters=parameters, command_context=command_context, study_version=STUDY_VERSION_9_2
            )
