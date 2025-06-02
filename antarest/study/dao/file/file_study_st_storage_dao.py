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
from typing_extensions import override

from antarest.study.business.model.sts_model import STStorage
from antarest.study.dao.api.st_storage_dao import STStorageDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudySTStorageDao(STStorageDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_all_st_storages(self) -> dict[str, dict[str, STStorage]]:
        raise NotImplementedError()

    @override
    def get_all_st_storages_for_area(self, area_id: str) -> Sequence[STStorage]:
        raise NotImplementedError()

    @override
    def get_st_storage(self, area_id: str, storage_id: str) -> STStorage:
        raise NotImplementedError()

    @override
    def st_storage_exists(self, area_id: str, storage_id: str) -> bool:
        raise NotImplementedError()

    @override
    def get_st_storage_pmax_injection(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_st_storage_pmax_withdrawal(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_st_storage_lower_rule_curve(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_st_storage_upper_rule_curve(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_st_storage_inflows(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_st_storage_cost_injection(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_st_storage_cost_withdrawal(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_st_storage_cost_level(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_st_storage_cost_variation_injection(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_st_storage_cost_variation_withdrawal(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def save_st_storage(self, area_id: str, st_storage: STStorage) -> None:
        raise NotImplementedError()

    @override
    def save_st_storages(self, area_id: str, storages: Sequence[STStorage]) -> None:
        raise NotImplementedError()

    @override
    def save_st_storage_pmax_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_st_storage_pmax_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_st_storage_upper_rule_curve(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_st_storage_inflows(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_st_storage_cost_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_st_storage_cost_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_st_storage_cost_level(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_st_storage_cost_variation_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_st_storage_cost_variation_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()