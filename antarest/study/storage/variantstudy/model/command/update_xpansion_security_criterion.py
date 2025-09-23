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

from antarest.study.business.model.xpansion_model import (
    XpansionSecurityCriterionUpdate,
    update_xpansion_security_criterion,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateXpansionSecurityCriterion(ICommand):
    """
    Command used to update xpansion security criterion
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_XPANSION_SECURITY_CRITERION

    # Command parameters
    # ==================

    criterion: XpansionSecurityCriterionUpdate

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        current_criterion = study_data.get_xpansion_security_criterion()
        new_criterion = update_xpansion_security_criterion(current_criterion, self.criterion)
        if self.criterion.patterns is not None:
            # Ensures the provided areas exist in the study
            study_data.checks_xpansion_security_criterion_coherence(new_criterion)
        study_data.save_xpansion_security_criterion(new_criterion)

        return command_succeeded(message="Xpansion security criterion updated successfully")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"criterion": self.criterion.model_dump(mode="json", exclude_none=True)},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
