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
from abc import ABC, abstractmethod
from pathlib import PurePosixPath
from typing import Any, cast

from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError, ResourceCreationNotAllowed, ResourceDeletionNotAllowed
from antarest.study.business.model.user_model import ResourceType
from antarest.study.dao.api.user_resources_dao import UserResourcesDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.user.user import User


def is_url_writeable(user_node: User, url: list[str]) -> bool:
    return url[0] not in [file.filename for file in user_node.registered_files]


class FileStudyUserResourceDao(UserResourcesDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def save_user_resource(self, resource_type: ResourceType, resource_path: PurePosixPath) -> None:
        url = [item for item in resource_path.parts if item]
        study_tree = self.get_file_study().tree
        user_node = cast(User, study_tree.get_node(["user"]))
        if not is_url_writeable(user_node, url):
            raise ResourceCreationNotAllowed(f"you are not allowed to create a resource here: {resource_path}")
        try:
            study_tree.get_node(["user"] + url)
        except ChildNotFoundError:
            # Creates the tree recursively to be able to create a resource inside a non-existing folder.
            last_value = b"" if resource_type == ResourceType.FILE else {}
            nested_dict: dict[str, Any] = {url[-1]: last_value}
            for key in reversed(url[:-1]):
                nested_dict = {key: nested_dict}
            study_tree.save({"user": nested_dict})
        else:
            raise ResourceCreationNotAllowed(f"the given resource already exists: {resource_path}")

    @override
    def delete_user_resource(self, resource_path: PurePosixPath) -> None:
        url = [item for item in resource_path.parts if item]
        study_tree = self.get_file_study().tree
        user_node = cast(User, study_tree.get_node(["user"]))
        if not is_url_writeable(user_node, url):
            raise ResourceDeletionNotAllowed(f"you are not allowed to delete this resource : {resource_path}")

        try:
            user_node.delete(url)
        except ChildNotFoundError:
            raise ResourceDeletionNotAllowed(f"the given path doesn't exist : {resource_path}")
