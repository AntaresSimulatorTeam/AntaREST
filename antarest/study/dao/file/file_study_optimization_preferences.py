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

from antarest.study.business.model.config.optimization_config import OPTIMIZATION_PATH, OptimizationPreferences
from antarest.study.dao.api.optimization_preferences_dao import OptimizationPreferencesDao
from antarest.study.storage.rawstudy.model.filesystem.config.optimization_preferences import (
    parse_optimization_preferences,
    serialize_optimization_preferences,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyOptimizationPreferencesDao(OptimizationPreferencesDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_optimization_preferences(self) -> OptimizationPreferences:
        file_study = self.get_file_study()

        tree_data = file_study.tree.get(OPTIMIZATION_PATH)

        return parse_optimization_preferences(tree_data)

    @override
    def save_optimization_preferences(self, config: OptimizationPreferences) -> None:
        file_study = self.get_file_study()

        optimization_preferences = serialize_optimization_preferences(config)

        # Include fields that are in the optimization part of the generaldata.ini file but not in the optimization class
        current_optimization_preferences = file_study.tree.get(OPTIMIZATION_PATH)
        optimization_preferences.update(
            {k: v for k, v in current_optimization_preferences.items() if k not in optimization_preferences}
        )

        file_study.tree.save(optimization_preferences, OPTIMIZATION_PATH)
