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

import json
from typing import Sequence

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, DistrictConfigNotFound
from antarest.study.business.model.district_model import District
from antarest.study.dao.api.district_dao import DistrictDao
from antarest.study.dao.database.model.district import DISTRICT_TABLE
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

        # Delete existing district if any
        session.execute(
            delete(DISTRICT_TABLE).where(
                (DISTRICT_TABLE.c.study_id == study_id) & (DISTRICT_TABLE.c.district_id == district.id)
            )
        )

        # Insert district with areas as JSON
        session.execute(
            insert(DISTRICT_TABLE).values(
                study_id=study_id,
                district_id=district.id,
                name=district.name,
                output=district.output,
                comments=district.comments,
                apply_filter=district.apply_filter,
                add_areas=json.dumps(district.add_areas),
                subtract_areas=json.dumps(district.subtract_areas),
            )
        )
        session.commit()

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

        session.execute(
            delete(DISTRICT_TABLE).where(
                (DISTRICT_TABLE.c.study_id == study_id) & (DISTRICT_TABLE.c.district_id == district_id)
            )
        )
        session.commit()

    @override
    def get_districts(self) -> Sequence[District]:
        """
        Returns the list of districts in this study.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        stmt = select(DISTRICT_TABLE).where(DISTRICT_TABLE.c.study_id == study_id)
        district_rows = session.execute(stmt).fetchall()

        return [
            District(
                id=row.district_id,
                name=row.name,
                output=row.output,
                comments=row.comments,
                apply_filter=row.apply_filter,
                add_areas=json.loads(row.add_areas),
                subtract_areas=json.loads(row.subtract_areas),
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

        stmt = select(DISTRICT_TABLE).where(
            (DISTRICT_TABLE.c.study_id == study_id) & (DISTRICT_TABLE.c.district_id == district_id)
        )
        row = session.execute(stmt).fetchone()
        if not row:
            raise DistrictConfigNotFound(district_id)

        return District(
            id=row.district_id,
            name=row.name,
            output=row.output,
            comments=row.comments,
            apply_filter=row.apply_filter,
            add_areas=json.loads(row.add_areas),
            subtract_areas=json.loads(row.subtract_areas),
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
