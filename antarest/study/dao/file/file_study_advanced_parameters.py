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

from antarest.study.business.model.config.advanced_parameters_model import AdvancedParameters
from antarest.study.dao.api.advanced_parameters_dao import AdvancedParametersDao
from antarest.study.storage.rawstudy.model.filesystem.config.advanced_parameters import (
    parse_advanced_parameters,
    serialize_advanced_parameters,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

GENERAL_DATA_PATH = ["settings", "generaldata"]


class FileStudyAdvancedParametersDao(AdvancedParametersDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_advanced_parameters(self) -> AdvancedParameters:
        file_study = self.get_file_study()
        general_data = file_study.tree.get(GENERAL_DATA_PATH)
        return parse_advanced_parameters(file_study.config.version, general_data)

    @override
    def save_advanced_parameters(self, parameters: AdvancedParameters) -> None:
        file_study = self.get_file_study()
        general_data = file_study.tree.get(GENERAL_DATA_PATH)
        new_content = serialize_advanced_parameters(file_study.config.version, parameters)
        general_data.update(new_content)
        file_study.tree.save(general_data, GENERAL_DATA_PATH)
