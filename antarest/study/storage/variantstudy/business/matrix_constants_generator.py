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

import tempfile
from pathlib import Path
from typing import Dict

import pandas as pd
from antares.study.version import StudyVersion
from filelock import FileLock

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.model import STUDY_VERSION_6_5, STUDY_VERSION_8_2
from antarest.study.storage.variantstudy.business import matrix_constants
from antarest.study.storage.variantstudy.business.matrix_constants.common import (
    FIXED_4_COLUMNS,
    FIXED_8_COLUMNS,
    NULL_MATRIX,
    NULL_SCENARIO_MATRIX,
)

# TODO: put index into variable

HYDRO_COMMON_CAPACITY_MAX_POWER_V7 = "hydro/common/capacity/max_power/v7"
HYDRO_COMMON_CAPACITY_RESERVOIR_V7 = "hydro/common/capacity/reservoir/v7"
HYDRO_COMMON_CAPACITY_RESERVOIR_V6 = "hydro/common/capacity/reservoir/v6"
HYDRO_COMMON_CAPACITY_INFLOW_PATTERN = "hydro/common/capacity/inflow_pattern"
HYDRO_COMMON_CAPACITY_CREDIT_MODULATION = "hydro/common/capacity/credit_modulations"
RESERVES_TS = "reserves"
MISCGEN_TS = "miscgen"
PREPRO_CONVERSION = "prepro/conversion"
PREPRO_DATA = "prepro/data"
THERMAL_PREPRO_DATA = "thermals/prepro/data"
THERMAL_PREPRO_MODULATION = "thermals/prepro/modulation"
LINK_V7 = "link_v7"
LINK_V8 = "link_v8"
LINK_DIRECT = "link_direct"
LINK_INDIRECT = "link_indirect"
NULL_MATRIX_NAME = "null_matrix"
EMPTY_SCENARIO_MATRIX = "empty_scenario_matrix"
ONES_SCENARIO_MATRIX = "ones_scenario_matrix"

# Binding constraint aliases
BINDING_CONSTRAINT_HOURLY_v86 = "empty_2nd_member_hourly_v86"
BINDING_CONSTRAINT_DAILY_WEEKLY_v86 = "empty_2nd_member_daily_or_weekly_v86"

BINDING_CONSTRAINT_HOURLY_v87 = "empty_2nd_member_hourly_v87"
BINDING_CONSTRAINT_DAILY_WEEKLY_v87 = "empty_2nd_member_daily_or_weekly_v87"

# Short-term storage aliases
ST_STORAGE_PMAX_INJECTION = ONES_SCENARIO_MATRIX
ST_STORAGE_PMAX_WITHDRAWAL = ONES_SCENARIO_MATRIX
ST_STORAGE_LOWER_RULE_CURVE = EMPTY_SCENARIO_MATRIX
ST_STORAGE_UPPER_RULE_CURVE = ONES_SCENARIO_MATRIX
ST_STORAGE_INFLOWS = EMPTY_SCENARIO_MATRIX

MATRIX_PROTOCOL_PREFIX = "matrix://"
_LOCK_FILE_NAME = "matrix_constant_init.lock"


# noinspection SpellCheckingInspection
class GeneratorMatrixConstants:
    def __init__(self, matrix_service: ISimpleMatrixService) -> None:
        self.hashes: Dict[str, str] = {}
        self.matrix_service: ISimpleMatrixService = matrix_service
        self._lock_dir = tempfile.gettempdir()

    def init_constant_matrices(
        self,
    ) -> None:
        with FileLock(str(Path(self._lock_dir) / _LOCK_FILE_NAME)):
            self.hashes[HYDRO_COMMON_CAPACITY_MAX_POWER_V7] = self.matrix_service.add_provider(
                lambda: matrix_constants.hydro.v7.max_power
            )
            self.hashes[HYDRO_COMMON_CAPACITY_RESERVOIR_V7] = self.matrix_service.add_provider(
                lambda: matrix_constants.hydro.v7.reservoir
            )
            self.hashes[HYDRO_COMMON_CAPACITY_RESERVOIR_V6] = self.matrix_service.add_provider(
                lambda: matrix_constants.hydro.v6.reservoir
            )
            self.hashes[HYDRO_COMMON_CAPACITY_INFLOW_PATTERN] = self.matrix_service.add_provider(
                lambda: matrix_constants.hydro.v7.inflow_pattern
            )
            self.hashes[HYDRO_COMMON_CAPACITY_CREDIT_MODULATION] = self.matrix_service.add_provider(
                lambda: matrix_constants.hydro.v7.credit_modulations
            )
            self.hashes[PREPRO_CONVERSION] = self.matrix_service.add_provider(
                lambda: matrix_constants.prepro.conversion
            )
            self.hashes[PREPRO_DATA] = self.matrix_service.add_provider(lambda: matrix_constants.prepro.data)
            self.hashes[THERMAL_PREPRO_DATA] = self.matrix_service.add_provider(
                lambda: matrix_constants.thermals.prepro.data
            )

            self.hashes[THERMAL_PREPRO_MODULATION] = self.matrix_service.add_provider(
                lambda: matrix_constants.thermals.prepro.modulation
            )
            self.hashes[LINK_V7] = self.matrix_service.add_provider(lambda: matrix_constants.link.v7.link)
            self.hashes[LINK_V8] = self.matrix_service.add_provider(lambda: matrix_constants.link.v8.link)
            self.hashes[LINK_DIRECT] = self.matrix_service.add_provider(lambda: matrix_constants.link.v8.direct)
            self.hashes[LINK_INDIRECT] = self.matrix_service.add_provider(lambda: matrix_constants.link.v8.indirect)

            self.hashes[NULL_MATRIX_NAME] = self.matrix_service.add_provider(lambda: NULL_MATRIX)
            self.hashes[EMPTY_SCENARIO_MATRIX] = self.matrix_service.add_provider(lambda: NULL_SCENARIO_MATRIX)
            self.hashes[RESERVES_TS] = self.matrix_service.add_provider(lambda: FIXED_4_COLUMNS)
            self.hashes[MISCGEN_TS] = self.matrix_service.add_provider(lambda: FIXED_8_COLUMNS)

        # Binding constraint matrices
        series_before_87 = matrix_constants.binding_constraint.series_before_v87
        self.hashes[BINDING_CONSTRAINT_HOURLY_v86] = self.matrix_service.add_provider(
            lambda: pd.DataFrame(series_before_87.default_bc_hourly)
        )
        self.hashes[BINDING_CONSTRAINT_DAILY_WEEKLY_v86] = self.matrix_service.add_provider(
            lambda: pd.DataFrame(series_before_87.default_bc_weekly_daily)
        )

        series_after_87 = matrix_constants.binding_constraint.series_after_v87
        self.hashes[BINDING_CONSTRAINT_HOURLY_v87] = self.matrix_service.add_provider(
            lambda: pd.DataFrame(series_after_87.default_bc_hourly)
        )
        self.hashes[BINDING_CONSTRAINT_DAILY_WEEKLY_v87] = self.matrix_service.add_provider(
            lambda: pd.DataFrame(series_after_87.default_bc_weekly_daily)
        )

        # Some short-term storage matrices use np.ones((8760, 1))
        self.hashes[ONES_SCENARIO_MATRIX] = self.matrix_service.add_provider(
            lambda: pd.DataFrame(matrix_constants.st_storage.series.pmax_injection)
        )

    def get_hydro_max_power(self, version: StudyVersion) -> str:
        if version > STUDY_VERSION_6_5:
            return MATRIX_PROTOCOL_PREFIX + self.hashes[HYDRO_COMMON_CAPACITY_MAX_POWER_V7]
        else:
            return MATRIX_PROTOCOL_PREFIX + self.hashes[NULL_MATRIX_NAME]

    def get_hydro_reservoir(self, version: StudyVersion) -> str:
        if version > STUDY_VERSION_6_5:
            return MATRIX_PROTOCOL_PREFIX + self.hashes[HYDRO_COMMON_CAPACITY_RESERVOIR_V7]
        return MATRIX_PROTOCOL_PREFIX + self.hashes[HYDRO_COMMON_CAPACITY_RESERVOIR_V6]

    def get_hydro_credit_modulations(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[HYDRO_COMMON_CAPACITY_CREDIT_MODULATION]

    def get_hydro_inflow_pattern(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[HYDRO_COMMON_CAPACITY_INFLOW_PATTERN]

    def get_prepro_conversion(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[PREPRO_CONVERSION]

    def get_prepro_data(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[PREPRO_DATA]

    def get_thermal_prepro_data(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[THERMAL_PREPRO_DATA]

    def get_thermal_prepro_modulation(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[THERMAL_PREPRO_MODULATION]

    def get_link(self, version: StudyVersion) -> str:
        if version < STUDY_VERSION_8_2:
            return MATRIX_PROTOCOL_PREFIX + self.hashes[LINK_V7]
        return MATRIX_PROTOCOL_PREFIX + self.hashes[LINK_V8]

    def get_link_direct(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[LINK_DIRECT]

    def get_link_indirect(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[LINK_INDIRECT]

    def get_null_matrix(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[NULL_MATRIX_NAME]

    def get_null_scenario_matrix(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[EMPTY_SCENARIO_MATRIX]

    def get_default_reserves(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[RESERVES_TS]

    def get_default_miscgen(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[MISCGEN_TS]

    def get_binding_constraint_hourly_86(self) -> str:
        """2D-matrix of shape (8784, 3), filled-in with zeros."""
        return MATRIX_PROTOCOL_PREFIX + self.hashes[BINDING_CONSTRAINT_HOURLY_v86]

    def get_binding_constraint_daily_weekly_86(self) -> str:
        """2D-matrix of shape (366, 3), filled-in with zeros."""
        return MATRIX_PROTOCOL_PREFIX + self.hashes[BINDING_CONSTRAINT_DAILY_WEEKLY_v86]

    def get_binding_constraint_hourly_87(self) -> str:
        """2D-matrix of shape (8784, 1), filled-in with zeros."""
        return MATRIX_PROTOCOL_PREFIX + self.hashes[BINDING_CONSTRAINT_HOURLY_v87]

    def get_binding_constraint_daily_weekly_87(self) -> str:
        """2D-matrix of shape (8784, 1), filled-in with zeros."""
        return MATRIX_PROTOCOL_PREFIX + self.hashes[BINDING_CONSTRAINT_DAILY_WEEKLY_v87]

    def get_st_storage_pmax_injection(self) -> str:
        """2D-matrix of shape (8760, 1), filled-in with ones."""
        return MATRIX_PROTOCOL_PREFIX + self.hashes[ST_STORAGE_PMAX_INJECTION]

    def get_st_storage_pmax_withdrawal(self) -> str:
        """2D-matrix of shape (8760, 1), filled-in with ones."""
        return MATRIX_PROTOCOL_PREFIX + self.hashes[ST_STORAGE_PMAX_WITHDRAWAL]

    def get_st_storage_lower_rule_curve(self) -> str:
        """2D-matrix of shape (8760, 1), filled-in with zeros."""
        return MATRIX_PROTOCOL_PREFIX + self.hashes[ST_STORAGE_LOWER_RULE_CURVE]

    def get_st_storage_upper_rule_curve(self) -> str:
        """2D-matrix of shape (8760, 1), filled-in with ones."""
        return MATRIX_PROTOCOL_PREFIX + self.hashes[ST_STORAGE_UPPER_RULE_CURVE]

    def get_st_storage_inflows(self) -> str:
        """2D-matrix of shape (8760, 1), filled-in with zeros."""
        return MATRIX_PROTOCOL_PREFIX + self.hashes[ST_STORAGE_INFLOWS]
