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
from typing import Iterable

from sqlalchemy import select
from typing_extensions import override

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.matrix_usage_provider import IMatrixUsageProvider
from antarest.matrixstore.model import MatrixReference
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.dao.database.models.area import LOAD_TABLE, MISC_GEN_TABLE, RESERVES_TABLE, SOLAR_TABLE, WIND_TABLE
from antarest.study.dao.database.models.binding_constraint import (
    BINDING_CONSTRAINT_EQ_MATRIX_TABLE,
    BINDING_CONSTRAINT_GT_MATRIX_TABLE,
    BINDING_CONSTRAINT_LT_MATRIX_TABLE,
    BINDING_CONSTRAINT_VALUES_MATRIX_TABLE,
)
from antarest.study.dao.database.models.hydro import (
    HYDRO_CREDIT_MODULATIONS_TABLE,
    HYDRO_ENERGY_TABLE,
    HYDRO_INFLOW_PATTERN_TABLE,
    HYDRO_MAX_DAILY_GEN_ENERGY_TABLE,
    HYDRO_MAX_DAILY_PUMP_ENERGY_TABLE,
    HYDRO_MAX_HOURLY_GEN_POWER_TABLE,
    HYDRO_MAX_HOURLY_PUMP_POWER_TABLE,
    HYDRO_MAXPOWER_TABLE,
    HYDRO_MINGEN_TABLE,
    HYDRO_MODULATION_TABLE,
    HYDRO_RESERVOIR_TABLE,
    HYDRO_RUN_OF_RIVER_TABLE,
    HYDRO_WATER_VALUES_TABLE,
)
from antarest.study.dao.database.models.link import (
    LINK_DIRECT_CAPACITY_TABLE,
    LINK_INDIRECT_CAPACITY_TABLE,
    LINK_SERIES_TABLE,
)
from antarest.study.dao.database.models.renewable import RENEWABLE_SERIES_TABLE
from antarest.study.dao.database.models.st_storage import (
    COST_INJECTION_TABLE,
    COST_LEVEL_TABLE,
    COST_VARIATION_INJECTION_TABLE,
    COST_VARIATION_WITHDRAWAL_TABLE,
    COST_WITHDRAWAL_TABLE,
    INFLOWS_TABLE,
    LOWER_RULE_CURVE_TABLE,
    PMAX_INJECTION_TABLE,
    PMAX_WITHDRAWAL_TABLE,
    ST_STORAGE_ADDITIONAL_CONSTRAINT_MATRIX_TABLE,
    UPPER_RULE_CURVE_TABLE,
)
from antarest.study.dao.database.models.thermal import (
    THERMAL_CO2_COST_TABLE,
    THERMAL_FUEL_COST_TABLE,
    THERMAL_MODULATION_TABLE,
    THERMAL_PREPRO_TABLE,
    THERMAL_SERIES_TABLE,
)
from antarest.study.dao.database.models.xpansion import XPANSION_CAPACITY_TABLE, XPANSION_WEIGHT_TABLE

MATRIX_TABLES = [
    LOAD_TABLE,
    SOLAR_TABLE,
    WIND_TABLE,
    RESERVES_TABLE,
    MISC_GEN_TABLE,
    LINK_SERIES_TABLE,
    LINK_DIRECT_CAPACITY_TABLE,
    LINK_INDIRECT_CAPACITY_TABLE,
    THERMAL_PREPRO_TABLE,
    THERMAL_MODULATION_TABLE,
    THERMAL_SERIES_TABLE,
    THERMAL_FUEL_COST_TABLE,
    THERMAL_CO2_COST_TABLE,
    RENEWABLE_SERIES_TABLE,
    PMAX_INJECTION_TABLE,
    PMAX_WITHDRAWAL_TABLE,
    LOWER_RULE_CURVE_TABLE,
    UPPER_RULE_CURVE_TABLE,
    INFLOWS_TABLE,
    COST_INJECTION_TABLE,
    COST_WITHDRAWAL_TABLE,
    COST_LEVEL_TABLE,
    COST_VARIATION_INJECTION_TABLE,
    COST_VARIATION_WITHDRAWAL_TABLE,
    ST_STORAGE_ADDITIONAL_CONSTRAINT_MATRIX_TABLE,
    HYDRO_MAXPOWER_TABLE,
    HYDRO_RESERVOIR_TABLE,
    HYDRO_ENERGY_TABLE,
    HYDRO_RUN_OF_RIVER_TABLE,
    HYDRO_MODULATION_TABLE,
    HYDRO_CREDIT_MODULATIONS_TABLE,
    HYDRO_INFLOW_PATTERN_TABLE,
    HYDRO_WATER_VALUES_TABLE,
    HYDRO_MINGEN_TABLE,
    HYDRO_MAX_HOURLY_GEN_POWER_TABLE,
    HYDRO_MAX_HOURLY_PUMP_POWER_TABLE,
    HYDRO_MAX_DAILY_GEN_ENERGY_TABLE,
    HYDRO_MAX_DAILY_PUMP_ENERGY_TABLE,
    XPANSION_CAPACITY_TABLE,
    XPANSION_WEIGHT_TABLE,
    BINDING_CONSTRAINT_VALUES_MATRIX_TABLE,
    BINDING_CONSTRAINT_LT_MATRIX_TABLE,
    BINDING_CONSTRAINT_GT_MATRIX_TABLE,
    BINDING_CONSTRAINT_EQ_MATRIX_TABLE,
]


class StudyDatabaseMatrixUsageProvider(IMatrixUsageProvider):
    def __init__(self, matrix_service: ISimpleMatrixService):
        matrix_service.register_usage_provider(self)

    @override
    def get_matrix_usage(self) -> Iterable[MatrixReference]:
        with db():
            for table in MATRIX_TABLES:
                stmt = select(table)
                rows = db.session.execute(stmt).fetchall()
                for row in rows:
                    description = f"Matrix used inside table {table.name}, for study {row.study_id}"
                    yield MatrixReference(matrix_id=row.matrix_id, use_description=description)
