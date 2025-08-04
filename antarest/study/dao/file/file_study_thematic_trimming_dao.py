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
from antarest.study.storage.rawstudy.model.filesystem.config.thematic_trimming import (
    parse_thematic_trimming,
    serialize_thematic_trimming,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

GENERAL_DATA_PATH = ["settings", "generaldata"]


class FileStudyThematicTrimmingDao(ThematicTrimmingDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_thematic_trimming(self) -> ThematicTrimming:
        file_study = self.get_file_study()
        general_data = file_study.tree.get(GENERAL_DATA_PATH)
        trimming_config = general_data.get("variables selection") or {}
        return parse_thematic_trimming(file_study.config.version, trimming_config)

    @override
    def save_thematic_trimming(self, trimming: ThematicTrimming) -> None:
        file_study = self.get_file_study()
        ini_content = serialize_thematic_trimming(file_study.config.version, trimming)
        file_study.tree.save(ini_content, ["settings", "generaldata", "variables selection"])
