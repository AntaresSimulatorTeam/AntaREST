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
from abc import ABC, abstractmethod
from pathlib import PurePosixPath
from typing import Iterator

from antarest.study.business.model.user_model import UserResourceDataCreation


class ReadOnlyUserResourcesDao(ABC):
    @abstractmethod
    def get_all_user_resources(self) -> Iterator[UserResourceDataCreation]:
        raise NotImplementedError()


class UserResourcesDao(ReadOnlyUserResourcesDao):
    @abstractmethod
    def save_user_resource(self, resource_data: UserResourceDataCreation) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_user_resource(self, resource_path: PurePosixPath) -> None:
        raise NotImplementedError()
