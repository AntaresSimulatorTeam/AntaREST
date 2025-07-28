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

from antarest.study.business.model.sts_model import (
    STStorage,
    STStorageAdditionalConstraint,
    STStorageAdditionalConstraintsMap,
)


class ReadOnlySTStorageDao(ABC):
    @abstractmethod
    def get_all_st_storages(self) -> dict[str, dict[str, STStorage]]:
        raise NotImplementedError()

    @abstractmethod
    def get_all_st_storages_for_area(self, area_id: str) -> Sequence[STStorage]:
        raise NotImplementedError()

    @abstractmethod
    def get_st_storage(self, area_id: str, storage_id: str) -> STStorage:
        raise NotImplementedError()

    @abstractmethod
    def st_storage_exists(self, area_id: str, storage_id: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def get_st_storage_pmax_injection(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_st_storage_pmax_withdrawal(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_st_storage_lower_rule_curve(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_st_storage_upper_rule_curve(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_st_storage_inflows(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_st_storage_cost_injection(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_st_storage_cost_withdrawal(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_st_storage_cost_level(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_st_storage_cost_variation_injection(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_st_storage_cost_variation_withdrawal(self, area_id: str, storage_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    ##########################
    # Additional constraints part
    ##########################

    @abstractmethod
    def get_all_st_storage_additional_constraints(self) -> STStorageAdditionalConstraintsMap:
        raise NotImplementedError()

    @abstractmethod
    def get_st_storage_additional_constraints(
        self, area_id: str, storage_id: str
    ) -> list[STStorageAdditionalConstraint]:
        raise NotImplementedError()


class STStorageDao(ReadOnlySTStorageDao):
    @abstractmethod
    def save_st_storage(self, area_id: str, st_storage: STStorage) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_st_storages(self, area_id: str, storages: Sequence[STStorage]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_st_storage_pmax_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_st_storage_pmax_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_st_storage_lower_rule_curve(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_st_storage_upper_rule_curve(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_st_storage_inflows(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_st_storage_cost_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_st_storage_cost_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_st_storage_cost_level(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_st_storage_cost_variation_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_st_storage_cost_variation_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_st_storage(self, area_id: str, storage: STStorage) -> None:
        raise NotImplementedError()

    ##########################
    # Additional constraints part
    ##########################

    @abstractmethod
    def delete_st_storage_additional_constraints(self, area_id: str, storage_id: str, constraints: list[str]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_st_storage_constraint_matrix(
        self, area_id: str, constraint_id: str, storage_id: str, series_id: str
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_st_storage_additional_constraints(
        self, area_id: str, storage_id: str, constraints: list[STStorageAdditionalConstraint]
    ) -> None:
        raise NotImplementedError()
