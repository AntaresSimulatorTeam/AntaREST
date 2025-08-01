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


from pydantic import model_validator
from typing_extensions import override

from antarest.study.business.model.config.adequacy_patch_model import (
    AdequacyPatchParametersUpdate,
    update_adequacy_patch_parameters,
    validate_adequacy_patch_parameters_against_version,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateAdequacyPatchParameters(ICommand):
    """
    Command used to update the adequacy-patch parameters of a study
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_ADEQUACY_PATCH_PARAMETERS

    # Command parameters
    # ==================
    parameters: AdequacyPatchParametersUpdate

    @model_validator(mode="after")
    def validate_against_version(self) -> "UpdateAdequacyPatchParameters":
        validate_adequacy_patch_parameters_against_version(self.study_version, self.parameters)
        return self

    @override
    def _apply_dao(self, study_data: StudyDao, listener: ICommandListener | None = None) -> CommandOutput:
        current_parameters = study_data.get_adequacy_patch_parameters()
        new_parameters = update_adequacy_patch_parameters(current_parameters, self.parameters)
        study_data.save_adequacy_patch_parameters(new_parameters)
        return command_succeeded("Adequacy-patch parameters updated successfully.")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"parameters": self.parameters.model_dump(exclude_none=True)},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> list[str]:
        return []
