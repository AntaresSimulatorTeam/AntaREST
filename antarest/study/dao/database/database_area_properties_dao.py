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

from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound
from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.dao.api.area_properties_dao import AreaPropertiesDao
from antarest.study.dao.database.common import (
    parse_frequency_filters,
    serialize_frequency_filters,
    validate_area_exists,
)
from antarest.study.dao.database.models import AREA_TABLE

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


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


class DatabaseAreaPropertiesDao(AreaPropertiesDao):
    """Database implementation of AreaPropertiesDao"""

    def __init__(self, study_id: str, db_session: Session) -> None:
        self._study_id = study_id
        self._db_session = db_session

    def get_study_id(self) -> str:
        """Get the study ID for database queries."""
        return self._study_id

    def get_session(self) -> Session:
        """Get the SQLAlchemy session for database operations."""
        return self._db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    @override
    def get_area_properties(self, area_id: str) -> AreaProperties:
        study_id = self.get_study_id()
        session = self.get_session()

        validate_area_exists(session, study_id, area_id)

        stmt = select(AREA_TABLE).where((AREA_TABLE.c.study_id == study_id) & (AREA_TABLE.c.area_id == area_id))

        row = session.execute(stmt).fetchone()
        if not row:
            raise AreaNotFound(area_id)
        return _convert_db_properties_to_model(row)

    @override
    def get_all_area_properties(self) -> dict[str, AreaProperties]:
        study_id = self.get_study_id()
        session = self.get_session()

        # Single query to get all areas and their properties
        stmt = select(AREA_TABLE).where(AREA_TABLE.c.study_id == study_id)
        rows = session.execute(stmt)
        return {row.area_id: _convert_db_properties_to_model(row) for row in rows}

    @override
    def save_area_properties(self, area_id: str, area_properties: AreaProperties) -> None:
        study_id = self.get_study_id()
        session = self.get_session()

        stmt_check = select(AREA_TABLE).where((AREA_TABLE.c.study_id == study_id) & (AREA_TABLE.c.area_id == area_id))
        existing_properties = session.execute(stmt_check).fetchone()
        if not existing_properties:
            raise AreaNotFound(area_id)

        stmt_update = (
            update(AREA_TABLE)
            .where((AREA_TABLE.c.study_id == study_id) & (AREA_TABLE.c.area_id == area_id))
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
        session.execute(stmt_update)
        session.commit()
