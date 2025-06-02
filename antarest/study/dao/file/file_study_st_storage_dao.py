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

from antarest.study.dao.api.st_storage_dao import STStorageDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudySTStorageDao(STStorageDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass
