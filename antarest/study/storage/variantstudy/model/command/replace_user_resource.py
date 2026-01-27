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
from typing import Any, Final, List, Optional

from pydantic import model_validator
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import override

from antarest.study.business.model.user_model import UserResourceDataCreation
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class ReplaceUserResource(ICommand):
    """
    Command used to save a resource inside the `user` folder.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REPLACE_USER_RESOURCE

    # Command parameters
    # ==================

    data: UserResourceDataCreation

    # version 2: change the structure of the `UserResourceDataCreation` class
    _SERIALIZATION_VERSION: Final[int] = 2

    @model_validator(mode="before")
    @classmethod
    def _validate_model(cls, values: dict[str, Any], info: ValidationInfo) -> dict[str, Any]:
        if info.context:
            version = info.context.version
            if version == 1:
                legacy_content = values["data"].get("content")
                if legacy_content:
                    # Saves the content inside the blob store and use the generated id inside the command
                    command_context: CommandContext = values["command_context"]
                    if isinstance(legacy_content, str):
                        legacy_content = legacy_content.encode("utf-8")
                    blob_id = command_context.blob_service.save(legacy_content)
                    del values["data"]["content"]
                    values["data"]["blob_id"] = blob_id

        return values

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        study_data.save_user_resource(self.data)
        return command_succeeded(message=f"{self.data.resource_type} {self.data.path} has been successfully created.")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            version=self._SERIALIZATION_VERSION,
            action=self.command_name.value,
            args={"data": self.data.model_dump(mode="json", exclude_none=True)},
            study_version=self.study_version,
        )

    @override
    def get_inner_blobs(self) -> List[str]:
        if self.data.blob_id:
            return [self.data.blob_id]
        return []
