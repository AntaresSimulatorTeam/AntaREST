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
from typing import Sequence

import pandas as pd

from antarest.study.business.model.renewable_cluster_model import RenewableCluster


class ReadOnlyRenewableDao(ABC):
    @abstractmethod
    def get_all_renewables(self) -> dict[str, dict[str, RenewableCluster]]:
        raise NotImplementedError()

    @abstractmethod
    def get_all_renewables_for_area(self, area_id: str) -> Sequence[RenewableCluster]:
        raise NotImplementedError()

    @abstractmethod
    def get_renewable(self, area_id: str, renewable_id: str) -> RenewableCluster:
        raise NotImplementedError()

    @abstractmethod
    def renewable_exists(self, area_id: str, renewable_id: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def get_renewable_series(self, area_id: str, renewable_id: str) -> pd.DataFrame:
        raise NotImplementedError()


class RenewableDao(ReadOnlyRenewableDao):
    @abstractmethod
    def save_renewable(self, area_id: str, renewable: RenewableCluster) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_renewables(self, area_id: str, renewables: Sequence[RenewableCluster]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_renewable_series(self, area_id: str, renewable_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_renewable(self, area_id: str, renewable: RenewableCluster) -> None:
        raise NotImplementedError()
