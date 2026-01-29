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
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Sequence

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, DistrictConfigNotFound
from antarest.study.business.model.district_model import District
from antarest.study.dao.api.district_dao import DistrictDao
from antarest.study.dao.database.models.district import DISTRICT_TABLE

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


def _convert_db_row_to_district(db_row: Any) -> District:
    return District(
        id=db_row.district_id,
        name=db_row.name,
        output=db_row.output,
        comments=db_row.comments,
        apply_filter=db_row.apply_filter,
        add_areas=json.loads(db_row.add_areas),
        subtract_areas=json.loads(db_row.subtract_areas),
    )


class DatabaseDistrictDao(DistrictDao):
    """
    Database implementation of DistrictDao.
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

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    @override
    def save_district(self, district: District) -> None:
        """
        Save a new district to a study.

        If the district already exists, it will be overwritten.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Validate that all areas exist
        invalid_areas = self.get_impl().get_invalid_area_ids(district.add_areas + district.subtract_areas)
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

    @override
    def remove_district(self, district_id: str) -> None:
        """
        Remove a district from a study.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        if not self.district_exists(district_id):
            raise DistrictConfigNotFound(f"District '{district_id}' does not exist in study '{study_id}'")

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

        return [_convert_db_row_to_district(row) for row in district_rows]

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

        return _convert_db_row_to_district(row)

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
