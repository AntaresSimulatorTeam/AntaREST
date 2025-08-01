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
import re

import pytest
from pydantic import ValidationError

from antarest.study.business.model.config.adequacy_patch_model import AdequacyPatchParametersUpdate
from antarest.study.model import STUDY_VERSION_8_2, STUDY_VERSION_8_3, STUDY_VERSION_9_2
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_adequacy_patch_parameters import (
    UpdateAdequacyPatchParameters,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestAdequacyPatchParameters:
    def test_nominal_case(self, empty_study_880: FileStudy, command_context: CommandContext):
        study = empty_study_880
        general_data_content = study.tree.get(["settings", "generaldata"])

        args = {"price_taking_order": "Load", "enable_adequacy_patch": True}
        parameters = AdequacyPatchParametersUpdate.model_validate(args)

        command = UpdateAdequacyPatchParameters(
            parameters=parameters, command_context=command_context, study_version=study.config.version
        )
        output = command.apply(study_data=study)
        assert output.status

        general_data_content["adequacy patch"]["price-taking-order"] = "Load"
        general_data_content["adequacy patch"]["include-adq-patch"] = True

        assert general_data_content == study.tree.get(["settings", "generaldata"])

    def test_error_cases(self, command_context: CommandContext):
        # Give fields that do not match the version
        with pytest.raises(ValidationError, match=re.escape("Adequacy patch parameters only exists in v8.3+ studies")):
            UpdateAdequacyPatchParameters(
                parameters=AdequacyPatchParametersUpdate(**{}),
                command_context=command_context,
                study_version=STUDY_VERSION_8_2,
            )

        parameters = AdequacyPatchParametersUpdate(**{"price_taking_order": "DENS"})
        with pytest.raises(
            ValidationError, match="Field price_taking_order is not a valid field for study version 8.3"
        ):
            UpdateAdequacyPatchParameters(
                parameters=parameters, command_context=command_context, study_version=STUDY_VERSION_8_3
            )

        parameters = AdequacyPatchParametersUpdate(**{"redispatch": True})
        with pytest.raises(ValidationError, match="Field redispatch is not a valid field for study version 9.2"):
            UpdateAdequacyPatchParameters(
                parameters=parameters, command_context=command_context, study_version=STUDY_VERSION_9_2
            )

        parameters = AdequacyPatchParametersUpdate(**{"ntc_between_physical_areas_out_adequacy_patch": True})
        with pytest.raises(
            ValidationError,
            match="Field ntc_between_physical_areas_out_adequacy_patch is not a valid field for study version 9.2",
        ):
            UpdateAdequacyPatchParameters(
                parameters=parameters, command_context=command_context, study_version=STUDY_VERSION_9_2
            )
