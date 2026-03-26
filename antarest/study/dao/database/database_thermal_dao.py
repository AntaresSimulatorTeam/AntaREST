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
from sqlalchemy import CursorResult, Row, Select, Table, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, ThermalClusterNotFound, ThermalClustersNotFound
from antarest.study.business.model.thermal_cluster_model import (
    ThermalCluster,
    initialize_thermal_cluster,
    validate_thermal_cluster_against_version,
)
from antarest.study.dao.api.thermal_dao import ThermalDao
from antarest.study.dao.common import AreaId, SeriesId, ThermalId
from antarest.study.dao.database.common import get_row_representation_as_dict, validate_area_exists
from antarest.study.dao.database.models.thermal import (
    THERMAL_CLUSTER_TABLE,
    THERMAL_CO2_COST_TABLE,
    THERMAL_FUEL_COST_TABLE,
    THERMAL_MODULATION_TABLE,
    THERMAL_PREPRO_TABLE,
    THERMAL_SERIES_TABLE,
)
from antarest.study.dao.database.sql_utils import upsert_multiple

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


class DatabaseThermalDao(ThermalDao):
    """
    Database implementation of ThermalDao.

    TODO: decide IDs handling, and in particular should we be case insensitive when searching
          for a cluster (same question for areas etc)
    """

    def __init__(self, study_id: str, db_session: Session) -> None:
        """
        Initialize DatabaseThermalDao with dependencies.

        Args:
            study_id: The study ID for database queries.
            db_session: SQLAlchemy session for database operations.
        """
        self._study_id = study_id
        self._db_session = db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    def _convert_db_row_to_thermal(self, row: Any) -> ThermalCluster:
        data = get_row_representation_as_dict(row)
        del data["study_id"]
        del data["area_id"]
        data["id"] = data.pop("thermal_id")
        cluster = ThermalCluster(**data)
        version = self.get_impl().get_version()
        validate_thermal_cluster_against_version(version, cluster)
        initialize_thermal_cluster(cluster, version)
        return cluster

    def _convert_thermal_cluster_to_row(self, area_id: str, cluster: ThermalCluster) -> dict[str, Any]:
        values = dict(study_id=self._study_id, area_id=area_id, **cluster.model_dump())
        values["thermal_id"] = values.pop("id").lower()
        return values

    def _get_thermal_matrix_row(self, area_id: str, thermal_id: str, table: Table) -> Row[Any] | None:
        study_id = self._study_id
        session = self._db_session
        stmt = select(table).where(
            (table.c.study_id == study_id) & (table.c.area_id == area_id) & (table.c.thermal_id == thermal_id)
        )
        return session.execute(stmt).fetchone()

    def _get_thermal_matrix(self, area_id: str, thermal_id: str, table: Table) -> pl.DataFrame:
        row = self._get_thermal_matrix_row(area_id, thermal_id, table)
        if not row:
            self._raise_the_right_exception({area_id: [thermal_id]})
        return self.get_impl().get_matrix(row.matrix_id)

    def _save_thermal_matrix(self, series: dict[AreaId, dict[ThermalId, SeriesId]], table: Table) -> None:
        study_id = self._study_id
        session = self._db_session

        try:
            values = []
            for area_id, value in series.items():
                for thermal_id, matrix_id in value.items():
                    data = {"study_id": study_id, "area_id": area_id, "thermal_id": thermal_id, "matrix_id": matrix_id}
                    values.append(data)
            upsert_multiple(session, table, values)
        except IntegrityError as e:
            invalid_data = {area_id: list(thermal_dict) for area_id, thermal_dict in series.items()}
            self._raise_the_right_exception(invalid_data, e)

        session.commit()

    def _raise_the_right_exception(
        self, data: dict[AreaId, list[ThermalId]], exc: IntegrityError | None = None
    ) -> NoReturn:
        # Checks if some areas are missing
        existing_ids = set(self.get_impl().get_all_area_ids())
        if invalid_areas := set(data) - existing_ids:
            raise AreaNotFound(*invalid_areas)

        # Means the issue lies in the thermals
        all_existing_thermals = self.get_all_thermals()
        invalid_thermal_dict = {}
        for area_id, value in all_existing_thermals.items():
            existing_thermals = set(value)
            if invalid_thermals := set(data[area_id]) - existing_thermals:
                invalid_thermal_dict[area_id] = invalid_thermals
        if len(invalid_thermal_dict) == 1:
            area_id = next(iter(invalid_thermal_dict))
            if len(invalid_thermal_dict[area_id]) == 1:
                # Only one thermal is missing, keep the clearer exception
                raise ThermalClusterNotFound(area_id, next(iter(invalid_thermal_dict[area_id]))) from exc
        raise ThermalClustersNotFound(invalid_thermal_dict) from exc

    @override
    def save_thermals(self, data: dict[AreaId, list[ThermalCluster]]) -> None:
        if not data:
            return

        session = self._db_session
        values = []
        for area_id, thermals in data.items():
            for thermal in thermals:
                values.append(self._convert_thermal_cluster_to_row(area_id, thermal))

        try:
            upsert_multiple(session=session, table=THERMAL_CLUSTER_TABLE, values=values)
        except IntegrityError as e:
            invalid_data = {area_id: [thermal.id.lower() for thermal in thermals] for area_id, thermals in data.items()}
            self._raise_the_right_exception(invalid_data, e)

        session.commit()

    @override
    def save_thermal_prepro(self, series: dict[AreaId, dict[ThermalId, SeriesId]]) -> None:
        self._save_thermal_matrix(series, THERMAL_PREPRO_TABLE)

    @override
    def save_thermal_modulation(self, series: dict[AreaId, dict[ThermalId, SeriesId]]) -> None:
        self._save_thermal_matrix(series, THERMAL_MODULATION_TABLE)

    @override
    def save_thermal_series(self, series: dict[AreaId, dict[ThermalId, SeriesId]]) -> None:
        self._save_thermal_matrix(series, THERMAL_SERIES_TABLE)

    @override
    def save_thermal_fuel_cost(self, series: dict[AreaId, dict[ThermalId, SeriesId]]) -> None:
        self._save_thermal_matrix(series, THERMAL_FUEL_COST_TABLE)

    @override
    def save_thermal_co2_cost(self, series: dict[AreaId, dict[ThermalId, SeriesId]]) -> None:
        self._save_thermal_matrix(series, THERMAL_CO2_COST_TABLE)

    @override
    def delete_thermal(self, area_id: str, thermal_id: str) -> None:
        study_id = self._study_id
        session = self._db_session

        result = session.execute(
            delete(THERMAL_CLUSTER_TABLE).where(
                (THERMAL_CLUSTER_TABLE.c.study_id == study_id)
                & (THERMAL_CLUSTER_TABLE.c.area_id == area_id)
                & (THERMAL_CLUSTER_TABLE.c.thermal_id == thermal_id)
            )
        )
        assert isinstance(result, CursorResult)
        if result.rowcount == 0:
            # Means the DELETE had no effect so the thermal did not exist
            self._raise_the_right_exception({area_id: [thermal_id]})

        session.commit()

    @override
    def get_all_thermals(self) -> dict[str, dict[str, ThermalCluster]]:
        study_id = self._study_id
        session = self._db_session

        stmt = select(THERMAL_CLUSTER_TABLE).where(THERMAL_CLUSTER_TABLE.c.study_id == study_id)
        rows = session.execute(stmt).fetchall()

        thermals_by_areas: dict[str, dict[str, ThermalCluster]] = {}
        for row in rows:
            thermal = self._convert_db_row_to_thermal(row)
            thermals_by_areas.setdefault(row.area_id, {})[thermal.id.lower()] = thermal
        return thermals_by_areas

    @override
    def get_all_thermals_for_area(self, area_id: str) -> Sequence[ThermalCluster]:
        study_id = self._study_id
        session = self._db_session

        stmt = select(THERMAL_CLUSTER_TABLE).where(
            (THERMAL_CLUSTER_TABLE.c.study_id == study_id) & (THERMAL_CLUSTER_TABLE.c.area_id == area_id)
        )
        rows = session.execute(stmt).fetchall()

        if not rows:
            # Ensures the area exists
            validate_area_exists(session, study_id, area_id)

        return [self._convert_db_row_to_thermal(row) for row in rows]

    def _select_thermal_cluster(self, area_id: str, thermal_id: str) -> Select[Any]:
        study_id = self._study_id
        return select(THERMAL_CLUSTER_TABLE).where(
            (THERMAL_CLUSTER_TABLE.c.study_id == study_id)
            & (THERMAL_CLUSTER_TABLE.c.area_id == area_id)
            & (THERMAL_CLUSTER_TABLE.c.thermal_id == thermal_id)
        )

    @override
    def get_thermal(self, area_id: str, thermal_id: str) -> ThermalCluster:
        session = self._db_session
        stmt = self._select_thermal_cluster(area_id, thermal_id)
        row = session.execute(stmt).fetchone()
        if not row:
            self._raise_the_right_exception({area_id: [thermal_id]})

        return self._convert_db_row_to_thermal(row)

    @override
    def thermal_exists(self, area_id: str, thermal_id: str) -> bool:
        session = self._db_session
        stmt = self._select_thermal_cluster(area_id, thermal_id)
        return session.execute(stmt).fetchone() is not None

    @override
    def get_thermal_prepro(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        return self._get_thermal_matrix(area_id, thermal_id, THERMAL_PREPRO_TABLE)

    @override
    def get_thermal_modulation(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        return self._get_thermal_matrix(area_id, thermal_id, THERMAL_MODULATION_TABLE)

    @override
    def get_thermal_series(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        return self._get_thermal_matrix(area_id, thermal_id, THERMAL_SERIES_TABLE)

    @override
    def get_thermal_fuel_cost(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        return self._get_thermal_matrix(area_id, thermal_id, THERMAL_FUEL_COST_TABLE)

    @override
    def get_thermal_co2_cost(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        return self._get_thermal_matrix(area_id, thermal_id, THERMAL_CO2_COST_TABLE)
