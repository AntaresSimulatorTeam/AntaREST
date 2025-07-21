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

from antarest.study.business.model.config.optimization_config import OptimizationPreferences


class ReadOnlyOptimizationPreferencesDao(ABC):
    @abstractmethod
    def get_optimization_preferences(self) -> OptimizationPreferences:
        raise NotImplementedError()


class OptimizationPreferencesDao(ReadOnlyOptimizationPreferencesDao):
    @abstractmethod
    def save_optimization_preferences(self, config: OptimizationPreferences) -> None:
        raise NotImplementedError()