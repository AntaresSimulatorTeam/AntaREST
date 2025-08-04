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

from antarest.study.business.model.thematic_trimming_model import ThematicTrimming


class ReadOnlyThematicTrimmingDao(ABC):
    @abstractmethod
    def get_thematic_trimming(self) -> ThematicTrimming:
        raise NotImplementedError()


class ThematicTrimmingDao(ReadOnlyThematicTrimmingDao):
    @abstractmethod
    def save_thematic_trimming(self, trimming: ThematicTrimming) -> None:
        raise NotImplementedError()
