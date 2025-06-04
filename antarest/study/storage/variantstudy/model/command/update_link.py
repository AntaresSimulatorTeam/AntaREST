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
from typing import Optional

from typing_extensions import override

from antarest.study.business.model.link_model import update_link
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.create_link import AbstractLinkCommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener


class UpdateLink(AbstractLinkCommand):
    """
    Command used to update a link between two areas.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_LINK

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        current_link = study_data.get_link(self.area1, self.area2)
        new_link = update_link(current_link, self.parameters)

        study_data.save_link(new_link)

        if self.series:
            study_data.save_link_series(self.area1, self.area2, str(self.series))

        if self.direct:
            study_data.save_link_direct_capacities(self.area1, self.area2, str(self.direct))

        if self.indirect:
            study_data.save_link_indirect_capacities(self.area1, self.area2, str(self.indirect))

        return command_succeeded(f"Link between '{self.area1}' and '{self.area2}' updated")
