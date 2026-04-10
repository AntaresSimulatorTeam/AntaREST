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
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import Row, Table, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from antarest.core.exceptions import AreaNotFound
from antarest.study.business.model.area_properties_model import FILTER_OPTIONS, FrequencyFilter, sort_filter_options
from antarest.study.dao.common import AreaSeriesMapping
from antarest.study.dao.database.models.area import AREA_TABLE
from antarest.study.dao.database.sql_utils import upsert_multiple

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


def validate_area_exists(session: Session, study_id: str, area_id: str) -> None:
    if not area_exists(session, study_id, area_id):
        raise AreaNotFound(area_id)


def area_exists(session: Session, study_id: str, area_id: str) -> bool:
    stmt = select(AREA_TABLE.c.area_id).where((AREA_TABLE.c.study_id == study_id) & (AREA_TABLE.c.area_id == area_id))
    return session.execute(stmt).fetchone() is not None


def get_row_representation_as_dict(row: Row[Any]) -> dict[str, Any]:
    return row._asdict()


def save_area_matrix(dao: "DatabaseStudyDao", series: AreaSeriesMapping, table: Table) -> None:
    session = dao.get_session()
    study_id = dao.get_study_id()

    try:
        values = []
        for area_id, series_id in series.items():
            data = {"study_id": study_id, "area_id": area_id, "matrix_id": series_id}
            values.append(data)
        upsert_multiple(session, table, values)

    except IntegrityError as e:
        invalid_ids = set(series) - set(dao.get_all_area_ids())
        if invalid_ids:
            raise AreaNotFound(*invalid_ids)
        else:
            # All areas exist. It means that the DB table does not contain the information.
            raise ValueError("One of the area matrices table is not filled as it should") from e

    session.commit()


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
    return cast(FrequencyFilter, value)


def serialize_frequency_filters(encoded_value: set[FrequencyFilter]) -> str:
    if isinstance(encoded_value, str):
        return encoded_value
    return ", ".join(sort_filter_options(encoded_value))
