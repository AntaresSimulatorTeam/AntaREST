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

from antarest.study.business.model.gems.system import GemsComponent, GemsSystem


class ReadOnlyGemsSystemDao(ABC):
    @abstractmethod
    def get_system(self) -> GemsSystem | None:
        raise NotImplementedError()

    @abstractmethod
    def get_components(self) -> list[GemsComponent]:
        raise NotImplementedError()


class GemsSystemDao(ReadOnlyGemsSystemDao):
    @abstractmethod
    def save_system(self, system: GemsSystem) -> None:
        """
        This method can only be used to add a system file to a study, not to replace it.
        """
        raise NotImplementedError()

    @abstractmethod
    def save_components(self, components: list[GemsComponent]) -> None:
        raise NotImplementedError()
