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

from antarest.launcher.model import LauncherLoadDTO


class AbstractLoad(ABC):
    def __init__(self):
        self.supports_load_caching = True

    @abstractmethod
    def get_load(self) -> LauncherLoadDTO:
        raise NotImplementedError()
