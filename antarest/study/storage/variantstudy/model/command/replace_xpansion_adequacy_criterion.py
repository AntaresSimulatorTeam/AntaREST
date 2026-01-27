# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from typing import Optional

from typing_extensions import override

from antarest.study.business.model.xpansion_model import (
    XpansionAdequacyCriterion,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class ReplaceXpansionAdequacyCriterion(ICommand):
    """
    Command used to replace xpansion adequacy criterion
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REPLACE_XPANSION_ADEQUACY_CRITERION

    # Command parameters
    # ==================

    criterion: XpansionAdequacyCriterion

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        study_data.save_xpansion_adequacy_criterion(self.criterion)
        return command_succeeded(message="Xpansion security criterion replaced successfully")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"criterion": self.criterion.model_dump(mode="json", exclude_none=True)},
            study_version=self.study_version,
        )
