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

from typing_extensions import override

from antarest.study.business.model.config.compatibility_parameters_model import CompatibilityParameters
from antarest.study.dao.api.compatibility_parameters_dao import ReadOnlyCompatibilityParametersDao
from antarest.study.storage.rawstudy.model.filesystem.config.compatibility_parameters import (
    parse_compatibility_parameters,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyCompatibilityParametersDao(ReadOnlyCompatibilityParametersDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_compatibility_parameters(self) -> CompatibilityParameters:
        file_study = self.get_file_study()
        try:
            data = file_study.tree.get(["settings", "generaldata", "compatibility"])
        except KeyError:
            data = {}
        return parse_compatibility_parameters(file_study.config.version, {"compatibility": data})
