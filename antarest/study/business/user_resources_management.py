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

from antarest.core.exceptions import UserResourceNotFound
from antarest.core.files_tree import FilesTree, FilesTreeBuilder
from antarest.study.business.model.user_model import (
    ResourceType,
    UserResourceDataCreation,
    UserResourceDataRemoval,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.remove_user_resource import RemoveUserResource
from antarest.study.storage.variantstudy.model.command.replace_user_resource import ReplaceUserResource
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def _build_tree(resources: list[UserResourceDataCreation]) -> FilesTree:
    builder = FilesTreeBuilder()
    for resource in resources:
        if resource.resource_type == ResourceType.FILE:
            builder.add_file(resource.path)
        else:
            builder.add_folder(resource.path)
    return builder.tree


class UserResourcesManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_all_user_resources(self, study: StudyInterface) -> FilesTree:
        user_resources = study.get_study_dao().get_all_user_resources()
        return _build_tree(user_resources)

    def get_user_resource(self, study: StudyInterface, path: PurePosixPath) -> bytes:
        return study.get_study_dao().get_user_resource(path)

    def delete_user_resource(self, study: StudyInterface, path: PurePosixPath) -> None:
        # First, we need to check if the resource exists
        for resource in study.get_study_dao().get_all_user_resources():
            if resource.path.is_relative_to(path):
                # Remove the existing resource
                command = RemoveUserResource(
                    data=UserResourceDataRemoval(path=path.as_posix()),
                    command_context=self._command_context,
                    study_version=study.version,
                )
                study.add_commands([command])
                return
        raise UserResourceNotFound(path.as_posix())

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
