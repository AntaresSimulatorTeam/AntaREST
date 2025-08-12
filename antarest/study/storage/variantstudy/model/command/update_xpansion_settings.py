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

from antarest.study.business.model.xpansion_model import XpansionSettingsUpdate, update_xpansion_settings
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
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
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        # Checks settings are correct
        study_data.checks_settings_are_correct(self.settings)

        current_settings = study_data.get_xpansion_settings()
        new_settings = update_xpansion_settings(current_settings, self.settings)
        study_data.save_xpansion_settings(new_settings)
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
