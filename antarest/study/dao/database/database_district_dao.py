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
from collections.abc import Sequence
from typing import Any

from antares.study.version import StudyVersion
from sqlalchemy import CursorResult, delete, select
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, DistrictConfigNotFound
from antarest.core.utils.sql_utils import upsert_one
from antarest.study.business.model.district_model import (
    District,
    check_district_complete,
    validate_district_against_version,
)
from antarest.study.dao.api.district_dao import DistrictDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.district import DISTRICT_TABLE


def _convert_db_row_to_district(db_row: Any, version: StudyVersion) -> District:
    district = District(
        id=db_row.district_id,
        name=db_row.name,
        output=db_row.output,
        comments=db_row.comments,
        apply_filter=db_row.apply_filter,
        add_areas=json.loads(db_row.add_areas),
        subtract_areas=json.loads(db_row.subtract_areas),
        filter_synthesis=db_row.filter_synthesis,
        filter_year_by_year=db_row.filter_year_by_year,
    )
    validate_district_against_version(version, district)
    return district


class DatabaseDistrictDao(DistrictDao, DatabaseDaoBase):
    """
    Database implementation of DistrictDao.
    """

    @override
    def save_district(self, district: District) -> None:
        """
        Save a new district to a study.

        If the district already exists, it will be overwritten.
        """
        study_data_id = self._study_data_id
        session = self._db_session

        # Validate that all areas exist
        invalid_areas = self.get_impl().get_invalid_area_ids(district.add_areas + district.subtract_areas)
        if invalid_areas:
            raise AreaNotFound(*invalid_areas)

        check_district_complete(district, self.get_impl().get_version())

        values = {
            "study_data_id": study_data_id,
            "district_id": district.id,
            "add_areas": json.dumps(district.add_areas),
            "subtract_areas": json.dumps(district.subtract_areas),
            **district.model_dump(mode="json", exclude={"add_areas", "subtract_areas", "id"}),
        }

        upsert_one(session, DISTRICT_TABLE, values)
        session.commit()

    @override
    def remove_district(self, district_id: str) -> None:
        """
        Remove a district from a study.
        """
        study_data_id = self._study_data_id
        session = self._db_session

        result = session.execute(
            delete(DISTRICT_TABLE).where(
                (DISTRICT_TABLE.c.study_data_id == study_data_id) & (DISTRICT_TABLE.c.district_id == district_id)
            )
        )
        assert isinstance(result, CursorResult)
        if result.rowcount == 0:
            # Means the DELETE had no effect so the district did not exist
            raise DistrictConfigNotFound(f"District '{district_id}' does not exist in study '{self._study_id}'")
        session.commit()

    @override
    def get_districts(self) -> Sequence[District]:
        """
        Returns the list of districts in this study.
        """
        study_data_id = self._study_data_id
        session = self._db_session

        stmt = select(DISTRICT_TABLE).where(DISTRICT_TABLE.c.study_data_id == study_data_id)
        district_rows = session.execute(stmt).fetchall()

        study_version = self.get_impl().get_version()
        return [_convert_db_row_to_district(row, study_version) for row in district_rows]

    @override
    def get_district(self, district_id: str) -> District:
        """
        Get the district with the given id.
        """
        study_data_id = self._study_data_id
        session = self._db_session

        stmt = select(DISTRICT_TABLE).where(
            (DISTRICT_TABLE.c.study_data_id == study_data_id) & (DISTRICT_TABLE.c.district_id == district_id)
        )
        row = session.execute(stmt).fetchone()
        if not row:
            raise DistrictConfigNotFound(district_id)

        study_version = self.get_impl().get_version()
        return _convert_db_row_to_district(row, study_version)

    @override
    def district_exists(self, district_id: str) -> bool:
        """
        Returns whether a district with the given id exists in the study.
        """
        study_data_id = self._study_data_id
        session = self._db_session

        stmt = select(DISTRICT_TABLE.c.district_id).where(
            (DISTRICT_TABLE.c.study_data_id == study_data_id) & (DISTRICT_TABLE.c.district_id == district_id)
        )
        return session.execute(stmt).fetchone() is not None
