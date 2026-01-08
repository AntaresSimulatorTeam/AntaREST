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
from typing import TYPE_CHECKING, Any, Iterator, cast

from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError, ResourceCreationNotAllowed, ResourceDeletionNotAllowed
from antarest.study.business.model.user_model import ResourceType, UserResourceDataCreation
from antarest.study.dao.api.user_resources_dao import UserResourcesDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.user.user import User

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao


def is_url_writeable(user_node: User, url: list[str]) -> bool:
    return url[0] not in [file.filename for file in user_node.registered_files]


class FileStudyUserResourceDao(UserResourcesDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_all_user_resources(self) -> Iterator[UserResourceDataCreation]:
        blob_service = self.get_impl()._blob_service
        user_path = self.get_file_study().config.study_path / "user"
        if user_path.exists():
            all_files = user_path.rglob("*")
            expansion_folder = user_path / "expansion"
            for file in all_files:
                if file.is_file() and not file.is_relative_to(expansion_folder):
                    content = file.read_bytes()
                    blob_id = blob_service.save(content)
                    yield UserResourceDataCreation(
                        path=PurePosixPath(file.relative_to(user_path).as_posix()),
                        resource_type=ResourceType.FILE,
                        blob_id=blob_id,
                    )

    @override
    def save_user_resource(self, resource_data: UserResourceDataCreation) -> None:
        url = [item for item in resource_data.path.parts if item]
        study_tree = self.get_file_study().tree
        user_node = cast(User, study_tree.get_node(["user"]))
        if not is_url_writeable(user_node, url):
            raise ResourceCreationNotAllowed(f"you are not allowed to create a resource here: {resource_data.path}")

        content: bytes | dict[str, str] = {}
        if resource_data.blob_id:
            # We need to fetch the actual content inside the blob store
            content = self.get_impl()._blob_service.get(resource_data.blob_id)

        # Creates the tree recursively to be able to create a resource inside a non-existing folder.
        nested_dict: dict[str, Any] = {url[-1]: content}
        for key in reversed(url[:-1]):
            nested_dict = {key: nested_dict}
        study_tree.save({"user": nested_dict})

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
