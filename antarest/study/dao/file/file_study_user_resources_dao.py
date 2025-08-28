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

from typing_extensions import override

from antarest.study.business.model.user_model import ResourceType
from antarest.study.dao.api.user_resources_dao import UserResourcesDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyUserResourceDao(UserResourcesDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def save_user_resource(self, resource_type: ResourceType, resource_path: PurePosixPath) -> None:
        raise NotImplementedError

    @override
    def delete_user_resource(self, resource_path: PurePosixPath) -> None:
        raise NotImplementedError
