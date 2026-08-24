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
from pathlib import PurePosixPath

from antarest.study.business.model.user_model import (
    ResourceType,
    UserResourceDataCreation,
    UserResourceDataRemoval,
    UserResourcesTree,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.remove_user_resource import RemoveUserResource
from antarest.study.storage.variantstudy.model.command.replace_user_resource import ReplaceUserResource
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class UserResourcesManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_all_user_resources_paths(self, study: StudyInterface) -> UserResourcesTree:
        user_resources = study.get_study_dao().get_all_user_resources()
        # result = {}

        """"
        class FolderTree(AntaresBaseModel):
            name: str
            directories: list["FolderTree"]
            files: list[str]
        
        class UserResourcesTree(AntaresBaseModel):
            directories: list[FolderTree]
            files: list[str]

        """

        sorted_resources = sorted(user_resources, key=lambda res: res.path)
        return [res.path.as_posix() for res in sorted_resources]

    def get_user_resource(self, study: StudyInterface, path: PurePosixPath) -> bytes:
        return study.get_study_dao().get_user_resource(path)

    def delete_user_resource(self, study: StudyInterface, path: PurePosixPath) -> None:
        command = RemoveUserResource(
            data=UserResourceDataRemoval(path=path.as_posix()),
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

    def replace_user_resource(
        self, study: StudyInterface, resource_type: ResourceType, path: PurePosixPath, content: bytes | None
    ) -> None:
        if content is None:
            blob_id = None
        else:
            blob_id = self._command_context.blob_service.save(content)

        data = UserResourceDataCreation(path=path, resource_type=resource_type, blob_id=blob_id)

        command = ReplaceUserResource(
            data=data,
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])
