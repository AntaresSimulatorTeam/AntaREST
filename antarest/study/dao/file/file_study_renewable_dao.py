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
from typing import Sequence, override

import pandas as pd

from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.dao.api.renewable_dao import RenewableDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyRenewableDao(RenewableDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_all_renewables(self) -> dict[str, dict[str, RenewableCluster]]:
        raise NotImplementedError()

    @override
    def get_all_renewables_for_area(self, area_id: str) -> Sequence[RenewableCluster]:
        raise NotImplementedError()

    @override
    def get_renewable(self, area_id: str, renewable_id: str) -> RenewableCluster:
        raise NotImplementedError()

    @override
    def renewable_exists(self, area_id: str, renewable_id: str) -> bool:
        raise NotImplementedError()

    @override
    def get_renewable_series(self, area_id: str, renewable_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def save_renewable(self, area_id: str, renewable: RenewableCluster) -> None:
        raise NotImplementedError()

    @override
    def save_renewables(self, area_id: str, renewables: Sequence[RenewableCluster]) -> None:
        raise NotImplementedError()

    @override
    def save_renewable_series(self, area_id: str, renewable_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def delete_renewable(self, area_id: str, renewable: RenewableCluster) -> None:
        raise NotImplementedError()
