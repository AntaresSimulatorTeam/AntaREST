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
from typing import List, Optional

from typing_extensions import override

from antarest.study.business.model.xpansion_model import XpansionSettingsUpdate
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.xpansion_common import (
    checks_settings_are_correct_and_returns_fields_to_exclude,
    get_xpansion_settings,
)
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateXpansionSettings(ICommand):
    """
    Command used to update xpansion settings
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_XPANSION_SETTINGS

    # Command parameters
    # ==================

    settings: XpansionSettingsUpdate

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        # Checks settings are correct
        excludes = checks_settings_are_correct_and_returns_fields_to_exclude(self.settings, study_data)

        # Updates settings
        current_settings = get_xpansion_settings(study_data)
        new_settings = self.settings.model_dump(mode="json", exclude_none=True, exclude={"sensitivity_config"})
        updated_settings = current_settings.model_copy(update=new_settings)
        config_obj = updated_settings.model_dump(mode="json", by_alias=True, exclude=excludes)
        study_data.tree.save(config_obj, ["user", "expansion", "settings"])

        # Updates sensitivity
        if self.settings.sensitivity_config:
            sensitivity_obj = self.settings.sensitivity_config.model_dump(mode="json", by_alias=True)
            study_data.tree.save(sensitivity_obj, ["user", "expansion", "sensitivity", "sensitivity_in"])

        return command_succeeded(message="Xpansion settings updated successfully")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "settings": self.settings.model_dump(mode="json", by_alias=True, exclude_none=True),
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
