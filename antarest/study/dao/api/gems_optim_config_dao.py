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

from antarest.study.business.model.gems.optim_config import GemsOptimConfig


class ReadOnlyGemsOptimConfigDao(ABC):
    @abstractmethod
    def get_optim_config(self) -> GemsOptimConfig | None:
        """
        Returns the optimization configuration of the study, or None if the study does not have one.
        """
        raise NotImplementedError()


class GemsOptimConfigDao(ReadOnlyGemsOptimConfigDao):
    @abstractmethod
    def save_optim_config(self, optim_config: GemsOptimConfig) -> None:
        """
        Saves the optimization configuration of the study, replacing the existing one if any.
        """
        raise NotImplementedError()
