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

from antarest.study.business.model.gems.system import (
    GemsAreaConnection,
    GemsComponent,
    GemsComponentConnection,
    GemsSystem,
    GemsThermalCapacityConnection,
)


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
        """
        Adds components to the system, or updates them if they already exist. Other components are left untouched.
        The parameters and properties of an updated component are replaced by the given ones.
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_components(self, component_ids: list[str]) -> None:
        """
        Removes components from the system, along with all their connections.
        """
        raise NotImplementedError()

    @abstractmethod
    def save_connections(self, connections: list[GemsComponentConnection]) -> None:
        """
        Adds connections between components to the system.
        Connections already in the system, whatever the order of their endpoints, are left untouched.
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_connections(self, connections: list[GemsComponentConnection]) -> None:
        """
        Removes connections between components from the system, whatever the order of their endpoints.
        """
        raise NotImplementedError()

    @abstractmethod
    def save_area_connections(self, connections: list[GemsAreaConnection]) -> None:
        """
        Adds area connections to the system.
        A port that is already connected to an area is connected to the new one instead.
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_area_connections(self, connections: list[GemsAreaConnection]) -> None:
        """
        Removes area connections from the system.
        """
        raise NotImplementedError()

    @abstractmethod
    def save_thermal_capacity_connections(self, connections: list[GemsThermalCapacityConnection]) -> None:
        """
        Adds thermal capacity connections to the system.
        A port that is already connected to a thermal cluster is connected to the new one instead.
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_thermal_capacity_connections(self, connections: list[GemsThermalCapacityConnection]) -> None:
        """
        Removes thermal capacity connections from the system.
        """
        raise NotImplementedError()
