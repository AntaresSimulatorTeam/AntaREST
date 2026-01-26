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
Database implementation of DistrictDao.

This module provides database-backed storage for districts when storage_mode=DATABASE.
"""

from typing import Sequence

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, DistrictConfigNotFound
from antarest.study.business.model.district_model import District, DistrictApplyFilter
from antarest.study.dao.api.district_dao import DistrictDao
from antarest.study.dao.database.model.district import DISTRICT_AREA_TABLE, DISTRICT_TABLE
from antarest.study.dao.database.models import AREA_TABLE


class DatabaseDistrictDao(DistrictDao):
    """
    Database implementation of DistrictDao.

    Note: Write operations do NOT commit transactions. The caller (service layer)
    is responsible for transaction management (commit/rollback).
    """

    def __init__(self, study_id: str, db_session: Session) -> None:
        """
        Initialize DatabaseDistrictDao with dependencies.

        Args:
            study_id: The study ID for database queries.
            db_session: SQLAlchemy session for database operations.
        """
        self._study_id = study_id
        self._db_session = db_session

    def get_study_id(self) -> str:
        """Get the study ID for database queries."""
        return self._study_id

    def get_session(self) -> Session:
        """Get the SQLAlchemy session for database operations."""
        return self._db_session

    @override
    def save_district(self, district: District) -> None:
        """
        Save a new district to a study.

        If the district already exists, it will be overwritten.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Validate that all areas exist
        invalid_areas = self._get_invalid_areas(district.add_areas + district.subtract_areas)
        if invalid_areas:
            raise AreaNotFound(*invalid_areas)

        # Delete existing district if any (cascade deletes area associations)
        session.execute(
            delete(DISTRICT_TABLE).where(
                (DISTRICT_TABLE.c.study_id == study_id) & (DISTRICT_TABLE.c.district_id == district.id)
            )
        )

        # Insert district
        session.execute(
            insert(DISTRICT_TABLE).values(
                study_id=study_id,
                district_id=district.id,
                name=district.name,
                output=district.output,
                comments=district.comments,
                apply_filter=district.apply_filter.value,
            )
        )

        # Insert area associations
        area_values = [
            {"study_id": study_id, "district_id": district.id, "area_id": area_id, "mode": "add"}
            for area_id in district.add_areas
        ] + [
            {"study_id": study_id, "district_id": district.id, "area_id": area_id, "mode": "subtract"}
            for area_id in district.subtract_areas
        ]
        if area_values:
            session.execute(insert(DISTRICT_AREA_TABLE), area_values)

    def _get_invalid_areas(self, areas: list[str]) -> list[str]:
        """Check which areas don't exist in the study."""
        if not areas:
            return []
        study_id = self.get_study_id()
        session = self.get_session()
        stmt = select(AREA_TABLE.c.area_id).where(
            (AREA_TABLE.c.study_id == study_id) & (AREA_TABLE.c.area_id.in_(areas))
        )
        existing = {row.area_id for row in session.execute(stmt)}
        return list(set(areas) - existing)

    @override
    def remove_district(self, district_id: str) -> None:
        """
        Remove a district from a study.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # CASCADE will delete area associations automatically
        session.execute(
            delete(DISTRICT_TABLE).where(
                (DISTRICT_TABLE.c.study_id == study_id) & (DISTRICT_TABLE.c.district_id == district_id)
            )
        )

    @override
    def get_districts(self) -> Sequence[District]:
        """
        Returns the list of districts in this study.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Get all districts
        stmt = select(DISTRICT_TABLE).where(DISTRICT_TABLE.c.study_id == study_id)
        district_rows = session.execute(stmt).fetchall()

        # Get all area associations
        stmt_areas = select(DISTRICT_AREA_TABLE).where(DISTRICT_AREA_TABLE.c.study_id == study_id)
        area_rows = session.execute(stmt_areas).fetchall()

        # Group areas by district_id
        areas_by_district: dict[str, dict[str, list[str]]] = {}
        for row in area_rows:
            areas_by_district.setdefault(row.district_id, {"add": [], "subtract": []})
            areas_by_district[row.district_id][row.mode].append(row.area_id)

        # Build District objects
        return [
            District(
                id=row.district_id,
                name=row.name,
                output=row.output,
                comments=row.comments,
                apply_filter=DistrictApplyFilter(row.apply_filter),
                add_areas=areas_by_district.get(row.district_id, {}).get("add", []),
                subtract_areas=areas_by_district.get(row.district_id, {}).get("subtract", []),
            )
            for row in district_rows
        ]

    @override
    def get_district(self, district_id: str) -> District:
        """
        Get the district with the given id.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Get district
        stmt = select(DISTRICT_TABLE).where(
            (DISTRICT_TABLE.c.study_id == study_id) & (DISTRICT_TABLE.c.district_id == district_id)
        )
        row = session.execute(stmt).fetchone()
        if not row:
            raise DistrictConfigNotFound(district_id)

        # Get area associations
        stmt_areas = select(DISTRICT_AREA_TABLE).where(
            (DISTRICT_AREA_TABLE.c.study_id == study_id) & (DISTRICT_AREA_TABLE.c.district_id == district_id)
        )
        add_areas = []
        subtract_areas = []
        for area_row in session.execute(stmt_areas):
            if area_row.mode == "add":
                add_areas.append(area_row.area_id)
            else:
                subtract_areas.append(area_row.area_id)

        return District(
            id=row.district_id,
            name=row.name,
            output=row.output,
            comments=row.comments,
            apply_filter=DistrictApplyFilter(row.apply_filter),
            add_areas=add_areas,
            subtract_areas=subtract_areas,
        )

    @override
    def district_exists(self, district_id: str) -> bool:
        """
        Returns whether a district with the given id exists in the study.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        stmt = select(DISTRICT_TABLE.c.district_id).where(
            (DISTRICT_TABLE.c.study_id == study_id) & (DISTRICT_TABLE.c.district_id == district_id)
        )
        return session.execute(stmt).fetchone() is not None
