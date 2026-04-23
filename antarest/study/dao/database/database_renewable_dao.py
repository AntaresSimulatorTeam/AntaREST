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
Database implementation of ThermalDao.
"""

from abc import abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, NoReturn

import polars as pl
from sqlalchemy import CursorResult, Select, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import (
    AreaNotFound,
    RenewableClusterNotFound,
    RenewableClustersNotFound,
)
from antarest.study.business.model.renewable_cluster_model import (
    RenewableCluster,
    validate_renewable_cluster_against_version,
)
from antarest.study.dao.api.renewable_dao import RenewableDao
from antarest.study.dao.common import AreaId, RenewableId, RenewableSeriesMapping
from antarest.study.dao.database.common import get_row_representation_as_dict, validate_area_exists
from antarest.study.dao.database.models.renewable import RENEWABLE_CLUSTER_TABLE, RENEWABLE_SERIES_TABLE
from antarest.study.dao.database.sql_utils import upsert_multiple, upsert_one
from antarest.study.storage.rawstudy.model.filesystem.matrix.simulator_default import default_scenario_hourly

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


class DatabaseRenewableDao(RenewableDao):
    """Database implementation of RenewableDao"""

    def __init__(self, study_id: str, db_session: Session) -> None:
        """
        Initialize DatabaseRenewableDao with dependencies.

        Args:
            study_id: The study ID for database queries.
            db_session: SQLAlchemy session for database operations.
        """
        self._study_id = study_id
        self._db_session = db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    def _convert_db_row_to_renewable(self, row: Any) -> RenewableCluster:
        data = get_row_representation_as_dict(row)
        del data["study_id"]
        del data["area_id"]
        data["id"] = data.pop("renewable_id")
        cluster = RenewableCluster(**data)
        version = self.get_impl().get_version()
        validate_renewable_cluster_against_version(version, cluster)
        return cluster

    def _convert_renewable_cluster_to_row(self, area_id: str, cluster: RenewableCluster) -> dict[str, Any]:
        values = dict(study_id=self._study_id, area_id=area_id, **cluster.model_dump())
        values["renewable_id"] = values.pop("id").lower()
        return values

    def _raise_the_right_renewable_exception(
        self, data: dict[AreaId, list[RenewableId]], exc: IntegrityError | None = None
    ) -> NoReturn:
        # Checks if some areas are missing
        existing_ids = set(self.get_impl().get_all_area_ids())
        if invalid_areas := set(data) - existing_ids:
            raise AreaNotFound(*invalid_areas)

        # Means the issue lies in the renewables
        all_existing_renewables = self.get_all_renewables()
        invalid_renewable_dict = {}
        for area_id, value in data.items():
            if invalid_renewables := set(data[area_id]) - set(all_existing_renewables.get(area_id, [])):
                invalid_renewable_dict[area_id] = invalid_renewables

        if len(invalid_renewable_dict) == 1:
            area_id = next(iter(invalid_renewable_dict))
            if len(invalid_renewable_dict[area_id]) == 1:
                # Only one renewable is missing, keep the clearer exception
                raise RenewableClusterNotFound(area_id, next(iter(invalid_renewable_dict[area_id]))) from exc

        elif not invalid_renewable_dict:
            # All renewables exist. It means that the DB table does not contain the information.
            raise ValueError("One of the renewable clusters table is not filled as it should") from exc

        raise RenewableClustersNotFound(invalid_renewable_dict) from exc

    @override
    def save_renewable(self, area_id: str, renewable: RenewableCluster) -> None:
        session = self._db_session

        values = self._convert_renewable_cluster_to_row(area_id, renewable)
        try:
            upsert_one(session, RENEWABLE_CLUSTER_TABLE, values)
        except IntegrityError as e:
            self._raise_the_right_renewable_exception({area_id: [renewable.id]}, e)

        session.commit()

    @override
    def save_renewables(self, data: dict[AreaId, list[RenewableCluster]]) -> None:
        if not data:
            return

        session = self._db_session
        values = []
        for area_id, renewables in data.items():
            for renewable in renewables:
                values.append(self._convert_renewable_cluster_to_row(area_id, renewable))

        try:
            upsert_multiple(session=session, table=RENEWABLE_CLUSTER_TABLE, values=values)
        except IntegrityError as e:
            invalid_data = {area_id: [renew.id.lower() for renew in renewables] for area_id, renewables in data.items()}
            self._raise_the_right_renewable_exception(invalid_data, e)

        session.commit()

    @override
    def save_renewable_series(self, series: RenewableSeriesMapping) -> None:
        study_id = self._study_id
        session = self._db_session

        try:
            values = []
            for area_id, value in series.items():
                for renewable_id, matrix_id in value.items():
                    data = {
                        "study_id": study_id,
                        "area_id": area_id,
                        "renewable_id": renewable_id,
                        "matrix_id": matrix_id,
                    }
                    values.append(data)
            upsert_multiple(session, RENEWABLE_SERIES_TABLE, values)
        except IntegrityError as e:
            invalid_data = {area_id: list(renewable_dict) for area_id, renewable_dict in series.items()}
            self._raise_the_right_renewable_exception(invalid_data, e)

        session.commit()

    @override
    def delete_renewable(self, area_id: str, renewable: RenewableCluster) -> None:
        study_id = self._study_id
        session = self._db_session
        renewable_id = renewable.id.lower()

        result = session.execute(
            delete(RENEWABLE_CLUSTER_TABLE).where(
                (RENEWABLE_CLUSTER_TABLE.c.study_id == study_id)
                & (RENEWABLE_CLUSTER_TABLE.c.area_id == area_id)
                & (RENEWABLE_CLUSTER_TABLE.c.renewable_id == renewable_id)
            )
        )
        assert isinstance(result, CursorResult)
        if result.rowcount == 0:
            # Means the DELETE had no effect so the renewable did not exist
            self._raise_the_right_renewable_exception({area_id: [renewable.id]})

        session.commit()

    @override
    def get_all_renewables(self) -> dict[str, dict[str, RenewableCluster]]:
        study_id = self._study_id
        session = self._db_session

        stmt = select(RENEWABLE_CLUSTER_TABLE).where(RENEWABLE_CLUSTER_TABLE.c.study_id == study_id)
        rows = session.execute(stmt).fetchall()

        renewables_by_areas: dict[str, dict[str, RenewableCluster]] = {}
        for row in rows:
            renewable = self._convert_db_row_to_renewable(row)
            renewables_by_areas.setdefault(row.area_id, {})[renewable.id.lower()] = renewable
        return renewables_by_areas

    @override
    def get_all_renewables_for_area(self, area_id: str) -> Sequence[RenewableCluster]:
        study_id = self._study_id
        session = self._db_session
        validate_area_exists(session, study_id, area_id)

        stmt = select(RENEWABLE_CLUSTER_TABLE).where(
            (RENEWABLE_CLUSTER_TABLE.c.study_id == study_id) & (RENEWABLE_CLUSTER_TABLE.c.area_id == area_id)
        )
        rows = session.execute(stmt).fetchall()
        return [self._convert_db_row_to_renewable(row) for row in rows]

    def _select_renewable_cluster(self, area_id: str, renewable_id: str) -> Select[Any]:
        study_id = self._study_id
        return select(RENEWABLE_CLUSTER_TABLE).where(
            (RENEWABLE_CLUSTER_TABLE.c.study_id == study_id)
            & (RENEWABLE_CLUSTER_TABLE.c.area_id == area_id)
            & (RENEWABLE_CLUSTER_TABLE.c.renewable_id == renewable_id)
        )

    @override
    def get_renewable(self, area_id: str, renewable_id: str) -> RenewableCluster:
        session = self._db_session
        stmt = self._select_renewable_cluster(area_id, renewable_id)
        row = session.execute(stmt).fetchone()
        if not row:
            self._raise_the_right_renewable_exception({area_id: [renewable_id]})

        return self._convert_db_row_to_renewable(row)

    @override
    def renewable_exists(self, area_id: str, renewable_id: str) -> bool:
        session = self._db_session
        stmt = self._select_renewable_cluster(area_id, renewable_id)
        return session.execute(stmt).fetchone() is not None

    @override
    def get_renewable_series(self, area_id: str, renewable_id: str) -> pl.DataFrame:
        study_id = self._study_id
        session = self._db_session
        stmt = select(RENEWABLE_SERIES_TABLE).where(
            (RENEWABLE_SERIES_TABLE.c.study_id == study_id)
            & (RENEWABLE_SERIES_TABLE.c.area_id == area_id)
            & (RENEWABLE_SERIES_TABLE.c.renewable_id == renewable_id)
        )
        row = session.execute(stmt).fetchone()
        if not row:
            self._raise_the_right_renewable_exception({area_id: [renewable_id]})

        return self.get_impl().get_matrix(row.matrix_id, default_empty_supplier=default_scenario_hourly)

    @override
    def get_all_renewables_series(self) -> RenewableSeriesMapping:
        study_id = self._study_id
        session = self._db_session
        stmt = select(RENEWABLE_SERIES_TABLE).where(RENEWABLE_SERIES_TABLE.c.study_id == study_id)
        rows = session.execute(stmt).fetchall()
        result: RenewableSeriesMapping = {}
        for row in rows:
            result.setdefault(row.area_id, {})[row.renewable_id] = row.matrix_id
        return result
