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

"""
Database implementation of AreaDao using SQLAlchemy Core.

This module provides database-backed storage for areas when storage_mode=DATABASE.
"""

from typing import Any

from sqlalchemy import CursorResult, select, update
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound
from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.dao.api.area_properties_dao import AreaPropertiesDao
from antarest.study.dao.database.common import (
    parse_frequency_filters,
    serialize_frequency_filters,
)
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.area import AREA_TABLE


def _convert_db_properties_to_model(db_row: Any) -> AreaProperties:
    return AreaProperties(
        energy_cost_unsupplied=db_row.energy_cost_unsupplied,
        energy_cost_spilled=db_row.energy_cost_spilled,
        non_dispatch_power=db_row.non_dispatch_power,
        dispatch_hydro_power=db_row.dispatch_hydro_power,
        other_dispatch_power=db_row.other_dispatch_power,
        spread_unsupplied_energy_cost=db_row.spread_unsupplied_energy_cost,
        spread_spilled_energy_cost=db_row.spread_spilled_energy_cost,
        filter_synthesis=parse_frequency_filters(db_row.filter_synthesis),
        filter_by_year=parse_frequency_filters(db_row.filter_by_year),
        adequacy_patch_mode=db_row.adequacy_patch_mode,
    )


class DatabaseAreaPropertiesDao(AreaPropertiesDao, DatabaseDaoBase):
    """Database implementation of AreaPropertiesDao"""

    @override
    def get_area_properties(self, area_id: str) -> AreaProperties:
        study_data_id = self._study_data_id
        session = self._db_session

        stmt = select(AREA_TABLE).where(
            (AREA_TABLE.c.study_data_id == study_data_id) & (AREA_TABLE.c.area_id == area_id)
        )

        row = session.execute(stmt).fetchone()
        if not row:
            raise AreaNotFound(area_id)
        return _convert_db_properties_to_model(row)

    @override
    def get_all_area_properties(self) -> dict[str, AreaProperties]:
        study_data_id = self._study_data_id
        session = self._db_session

        # Single query to get all areas and their properties
        stmt = select(AREA_TABLE).where(AREA_TABLE.c.study_data_id == study_data_id)
        rows = session.execute(stmt)
        return {row.area_id: _convert_db_properties_to_model(row) for row in rows}

    @override
    def save_area_properties(self, area_id: str, area_properties: AreaProperties) -> None:
        study_data_id = self._study_data_id
        session = self._db_session

        stmt_update = (
            update(AREA_TABLE)
            .where((AREA_TABLE.c.study_data_id == study_data_id) & (AREA_TABLE.c.area_id == area_id))
            .values(
                energy_cost_unsupplied=area_properties.energy_cost_unsupplied,
                energy_cost_spilled=area_properties.energy_cost_spilled,
                non_dispatch_power=area_properties.non_dispatch_power,
                dispatch_hydro_power=area_properties.dispatch_hydro_power,
                other_dispatch_power=area_properties.other_dispatch_power,
                spread_unsupplied_energy_cost=area_properties.spread_unsupplied_energy_cost,
                spread_spilled_energy_cost=area_properties.spread_spilled_energy_cost,
                filter_synthesis=serialize_frequency_filters(area_properties.filter_synthesis),
                filter_by_year=serialize_frequency_filters(area_properties.filter_by_year),
                adequacy_patch_mode=area_properties.adequacy_patch_mode,
            )
        )
        result = session.execute(stmt_update)
        assert isinstance(result, CursorResult)
        if result.rowcount == 0:
            # Means the update had no effect so the area did not exist
            raise AreaNotFound(area_id)
        session.commit()
