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

from antarest.study.business.model.binding_constraint_model import BindingConstraint


class ReadOnlyConstraintDao(ABC):
    @abstractmethod
    def get_all_constraints(self) -> dict[str, BindingConstraint]:
        raise NotImplementedError()

    @abstractmethod
    def get_constraint(self, constraint_id: str) -> BindingConstraint:
        raise NotImplementedError()

    @abstractmethod
    def get_constraint_values_matrix(self, constraint_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_constraint_less_term_matrix(self, constraint_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_constraint_greater_term_matrix(self, constraint_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_constraint_equal_term_matrix(self, constraint_id: str) -> pd.DataFrame:
        raise NotImplementedError()


class ConstraintDao(ReadOnlyConstraintDao):
    @abstractmethod
    def save_constraints(self, constraints: Sequence[BindingConstraint]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_constraint_values_matrix(self, constraint_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_constraint_less_term_matrix(self, constraint_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_constraint_greater_term_matrix(self, constraint_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_constraint_equal_term_matrix(self, constraint_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_constraints(self, constraints: list[BindingConstraint]) -> None:
        raise NotImplementedError()
