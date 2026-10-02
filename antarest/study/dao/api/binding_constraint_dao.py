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
from collections.abc import Sequence

import polars as pl

from antarest.study.business.model.binding_constraint_model import BindingConstraint, ConstraintId
from antarest.study.dao.common import BindingConstraintSeriesMapping


class ReadOnlyConstraintDao(ABC):
    @abstractmethod
    def get_all_constraints(self) -> dict[ConstraintId, BindingConstraint]:
        raise NotImplementedError()

    @abstractmethod
    def get_constraint(self, constraint_id: ConstraintId) -> BindingConstraint:
        raise NotImplementedError()

    @abstractmethod
    def get_constraint_values_matrix(self, constraint_id: ConstraintId) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_constraint_less_term_matrix(self, constraint_id: ConstraintId) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_constraint_greater_term_matrix(self, constraint_id: ConstraintId) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_constraint_equal_term_matrix(self, constraint_id: ConstraintId) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_all_constraint_values_matrix(self) -> BindingConstraintSeriesMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_constraint_less_term_matrix(self) -> BindingConstraintSeriesMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_constraint_greater_term_matrix(self) -> BindingConstraintSeriesMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_constraint_equal_term_matrix(self) -> BindingConstraintSeriesMapping:
        raise NotImplementedError()


class ConstraintDao(ReadOnlyConstraintDao):
    @abstractmethod
    def save_constraints(self, constraints: Sequence[BindingConstraint]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_constraint_values_matrix(self, series: BindingConstraintSeriesMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_constraint_less_term_matrix(self, series: BindingConstraintSeriesMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_constraint_greater_term_matrix(self, series: BindingConstraintSeriesMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_constraint_equal_term_matrix(self, series: BindingConstraintSeriesMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_constraints(self, constraints: list[BindingConstraint]) -> None:
        raise NotImplementedError()
