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

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateComments(ICommand):
    """
    Command used to update the comments of the study located in `settings/comments.txt`.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_COMMENTS

    # Command parameters
    # ==================

    comments: str

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        replace_comment_data: JSON = {"settings": {"comments": self.comments.encode("utf-8")}}

        study_data.tree.save(replace_comment_data)

        return command_succeeded(message=f"Comment '{self.comments}' has been successfully replaced.")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_COMMENTS.value,
            args={
                "comments": self.comments,
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
