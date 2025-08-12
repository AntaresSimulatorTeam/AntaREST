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


from antarest.study.business.model.config.adequacy_patch_model import (
    AdequacyPatchParameters,
    AdequacyPatchParametersUpdate,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.update_adequacy_patch_parameters import (
    UpdateAdequacyPatchParameters,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class AdequacyPatchManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_adequacy_patch_parameters(self, study: StudyInterface) -> AdequacyPatchParameters:
        """
        Get adequacy patch parameters for the webapp form
        """
        return study.get_study_dao().get_adequacy_patch_parameters()

    def set_adequacy_patch_parameters(
        self, study: StudyInterface, parameters: AdequacyPatchParametersUpdate
    ) -> AdequacyPatchParameters:
        """
        Set adequacy patch config from the webapp form
        """
        command = UpdateAdequacyPatchParameters(
            parameters=parameters, command_context=self._command_context, study_version=study.version
        )
        study.add_commands([command])
        return self.get_adequacy_patch_parameters(study)
