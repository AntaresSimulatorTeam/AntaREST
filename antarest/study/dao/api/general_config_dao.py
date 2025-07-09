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

from antarest.study.business.model.config.general_model import GeneralConfig


class ReadOnlyGeneralConfigDao(ABC):
    @abstractmethod
    def get_general_config(self) -> GeneralConfig:
        raise NotImplementedError()


class GeneralConfigDao(ReadOnlyGeneralConfigDao):
    @abstractmethod
    def update_general_config(self, config: GeneralConfig) -> None:
        raise NotImplementedError()
