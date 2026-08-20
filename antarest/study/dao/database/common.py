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
import json
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Sequence, cast

from sqlalchemy import Row, Table, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from antarest.core.exceptions import AreaNotFound
from antarest.core.utils.sql_utils import upsert_multiple
from antarest.dbmodel import get_row_representation_as_dict
from antarest.study.business.model.area_properties_model import FILTER_OPTIONS, FrequencyFilter, sort_filter_options
from antarest.study.business.model.reserve_certification_model import (
    ReserveCertification,
)
from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetries
from antarest.study.dao.common import AreaSeriesMapping, ReserveSymmetriesMapping
from antarest.study.dao.database.models.area import AREA_TABLE
from antarest.study.dao.database.models.st_storage_reserve_symmetries import ST_STORAGE_RESERVE_SYMMETRIES_TABLE
from antarest.study.dao.database.models.thermal_reserve_symmetries import THERMAL_RESERVE_SYMMETRIES_TABLE

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


def validate_area_exists(session: Session, study_data_id: int, area_id: str) -> None:
    if not area_exists(session, study_data_id, area_id):
        raise AreaNotFound(area_id)


def area_exists(session: Session, study_data_id: int, area_id: str) -> bool:
    stmt = select(AREA_TABLE.c.area_id).where(
        (AREA_TABLE.c.study_data_id == study_data_id) & (AREA_TABLE.c.area_id == area_id)
    )
    return session.execute(stmt).fetchone() is not None


def save_area_matrix(dao: "DatabaseStudyDao", series: AreaSeriesMapping, table: Table) -> None:
    session = dao._db_session
    study_data_id = dao._study_data_id

    try:
        values = []
        for area_id, series_id in series.items():
            data = {"study_data_id": study_data_id, "area_id": area_id, "matrix_id": series_id}
            values.append(data)
        upsert_multiple(session, table, values)

    except IntegrityError as e:
        session.rollback()
        invalid_ids = set(series) - set(dao.get_all_area_ids())
        if invalid_ids:
            raise AreaNotFound(*invalid_ids)
        else:
            # All areas exist. It means that the DB table does not contain the information.
            raise ValueError("One of the area matrices table is not filled as it should") from e

    session.commit()


def get_all_area_matrices(study_data_id: int, session: Session, table: Table) -> AreaSeriesMapping:
    stmt = select(table).where((table.c.study_data_id == study_data_id))
    rows = session.execute(stmt).fetchall()
    return {row.area_id: row.matrix_id for row in rows}


"""
Parse and Serialize the `FrequencyFilter` attribute which is stored as Text inside DB.
"""


def parse_frequency_filters(value: str) -> set[FrequencyFilter]:
    if not value:
        return set()
    return {_validate_filter(item.strip()) for item in value.split(",")}


def _validate_filter(value: str) -> FrequencyFilter:
    if value not in FILTER_OPTIONS:
        raise ValueError(f"Invalid filter {value}, expected one of {','.join(FILTER_OPTIONS)}.")
    return value


def serialize_frequency_filters(encoded_value: set[FrequencyFilter]) -> str:
    if isinstance(encoded_value, str):
        return encoded_value
    return ", ".join(sort_filter_options(encoded_value))


"""
Reserve types
"""


def _convert_row_to_symmetries(row: Row[Any]) -> ReserveSymmetries:
    return cast(ReserveSymmetries, json.loads(row.symmetries))


class ReserveObjectType(StrEnum):
    THERMAL = "thermal"
    ST_STORAGE = "st_storage"

    def _db_key(self) -> str:
        if self == ReserveObjectType.THERMAL:
            return "thermal_id"
        else:
            return "st_storage_id"

    def db_symmetry_table(self) -> Table:
        if self == ReserveObjectType.THERMAL:
            return THERMAL_RESERVE_SYMMETRIES_TABLE
        else:
            return ST_STORAGE_RESERVE_SYMMETRIES_TABLE

    def convert_symmetry_to_row(
        self, study_data_id: int, area_id: str, object_id: str, symmetries: ReserveSymmetries
    ) -> dict[str, Any]:
        return {
            "study_data_id": study_data_id,
            "area_id": area_id,
            "symmetries": json.dumps(symmetries),
            self._db_key(): object_id,
        }

    def convert_all_rows_to_symmetries(self, rows: Sequence[Row[Any]]) -> dict[str, ReserveSymmetries]:
        result = {}
        for row in rows:
            row_as_dict = get_row_representation_as_dict(row)
            result[row_as_dict[self._db_key()]] = _convert_row_to_symmetries(row)
        return result

    def convert_all_rows_to_dict_of_symmetries(self, rows: Sequence[Row[Any]]) -> ReserveSymmetriesMapping:
        result: ReserveSymmetriesMapping = {}
        for row in rows:
            row_as_dict = get_row_representation_as_dict(row)
            result.setdefault(row.area_id, {})[row_as_dict[self._db_key()]] = _convert_row_to_symmetries(row)
        return result

    def convert_certification_to_row(
        self, study_data_id: int, area_id: str, object_id: str, reserve_id: str, certification: ReserveCertification
    ) -> dict[str, Any]:
        return {
            "study_data_id": study_data_id,
            "area_id": area_id,
            "reserve_id": reserve_id,
            self._db_key(): object_id,
            **certification.model_dump(),
        }

    def convert_row_to_mapping(self, row: Row[Any]) -> dict[str, Any]:
        data = get_row_representation_as_dict(row)
        for key in ("study_data_id", "area_id", self._db_key(), "reserve_id"):
            del data[key]
        return data
