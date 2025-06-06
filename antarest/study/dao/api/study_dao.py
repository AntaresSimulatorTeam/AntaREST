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
from abc import abstractmethod
from typing import Sequence

import pandas as pd
from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.study.business.model.link_model import Link
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.api.link_dao import LinkDao, ReadOnlyLinkDao
from antarest.study.dao.api.renewable_dao import ReadOnlyRenewableDao, RenewableDao
from antarest.study.dao.api.thermal_dao import ReadOnlyThermalDao, ThermalDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class ReadOnlyStudyDao(ReadOnlyLinkDao, ReadOnlyThermalDao, ReadOnlyRenewableDao):
    @abstractmethod
    def get_version(self) -> StudyVersion:
        raise NotImplementedError()


class StudyDao(ReadOnlyStudyDao, LinkDao, ThermalDao, RenewableDao):
    """
    Abstraction for access to study data. Handles all reading
    and writing from underlying storage format.
    """

    def read_only(self) -> ReadOnlyStudyDao:
        """
        Returns a read only version of this DAO,
        to ensure it's not used for writing.
        """
        return ReadOnlyAdapter(self)

    @abstractmethod
    def get_file_study(self) -> FileStudy:
        """
        To ease transition, to be removed when all goes through other methods
        """
        raise NotImplementedError()


class ReadOnlyAdapter(ReadOnlyStudyDao):
    """
    Adapts a full DAO as a read only DAO without modification methods.
    """

    def __init__(self, adaptee: StudyDao):
        self._adaptee = adaptee

    @override
    def get_version(self) -> StudyVersion:
        return self._adaptee.get_version()

    @override
    def get_links(self) -> Sequence[Link]:
        return self._adaptee.get_links()

    @override
    def get_link(self, area1_id: str, area2_id: str) -> Link:
        return self._adaptee.get_link(area1_id, area2_id)

    @override
    def link_exists(self, area1_id: str, area2_id: str) -> bool:
        return self._adaptee.link_exists(area1_id, area2_id)

    @override
    def get_all_thermals(self) -> dict[str, dict[str, ThermalCluster]]:
        return self._adaptee.get_all_thermals()

    @override
    def get_all_thermals_for_area(self, area_id: str) -> Sequence[ThermalCluster]:
        return self._adaptee.get_all_thermals_for_area(area_id)

    @override
    def get_thermal(self, area_id: str, thermal_id: str) -> ThermalCluster:
        return self._adaptee.get_thermal(area_id, thermal_id)

    @override
    def thermal_exists(self, area_id: str, thermal_id: str) -> bool:
        return self._adaptee.thermal_exists(area_id, thermal_id)

    @override
    def get_thermal_prepro(self, area_id: str, thermal_id: str) -> pd.DataFrame:
        return self._adaptee.get_thermal_prepro(area_id, thermal_id)

    @override
    def get_thermal_modulation(self, area_id: str, thermal_id: str) -> pd.DataFrame:
        return self._adaptee.get_thermal_modulation(area_id, thermal_id)

    @override
    def get_thermal_series(self, area_id: str, thermal_id: str) -> pd.DataFrame:
        return self._adaptee.get_thermal_series(area_id, thermal_id)

    @override
    def get_thermal_fuel_cost(self, area_id: str, thermal_id: str) -> pd.DataFrame:
        return self._adaptee.get_thermal_fuel_cost(area_id, thermal_id)

    @override
    def get_thermal_co2_cost(self, area_id: str, thermal_id: str) -> pd.DataFrame:
        return self._adaptee.get_thermal_co2_cost(area_id, thermal_id)

    @override
    def get_all_renewables(self) -> dict[str, dict[str, RenewableCluster]]:
        return self._adaptee.get_all_renewables()

    @override
    def get_all_renewables_for_area(self, area_id: str) -> Sequence[RenewableCluster]:
        return self._adaptee.get_all_renewables_for_area(area_id)

    @override
    def get_renewable(self, area_id: str, renewable_id: str) -> RenewableCluster:
        return self._adaptee.get_renewable(area_id, renewable_id)

    @override
    def renewable_exists(self, area_id: str, renewable_id: str) -> bool:
        return self._adaptee.renewable_exists(area_id, renewable_id)

    @override
    def get_renewable_series(self, area_id: str, renewable_id: str) -> pd.DataFrame:
        return self._adaptee.get_renewable_series(area_id, renewable_id)
