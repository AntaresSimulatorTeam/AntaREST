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
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyAdvancedParametersDao(AdvancedParametersDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_advanced_parameters(self) -> AdvancedParameters:
        raise NotImplementedError()

    @override
    def save_advanced_parameters(self, parameters: AdvancedParameters) -> None:
        raise NotImplementedError()
