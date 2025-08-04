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

from typing_extensions import override

from antarest.study.business.model.thematic_trimming_model import ThematicTrimming
from antarest.study.dao.api.thematic_trimming_dao import ThematicTrimmingDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyThematicTrimmingDao(ThematicTrimmingDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_thematic_trimming(self) -> ThematicTrimming:
        raise NotImplementedError

    @override
    def save_thematic_trimming(self, trimming: ThematicTrimming) -> None:
        raise NotImplementedError
