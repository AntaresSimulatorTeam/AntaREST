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
from typing import TYPE_CHECKING, Any, Sequence

import polars as pl
from sqlalchemy import Row, Table, delete, insert, select, update
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import ThermalClusterNotFound
from antarest.study.business.model.thermal_cluster_model import (
    ThermalCluster,
    initialize_thermal_cluster,
    validate_thermal_cluster_against_version,
)
from antarest.study.dao.api.thermal_dao import ThermalDao
from antarest.study.dao.database.common import validate_area_exists
from antarest.study.dao.database.models.thermal import (
    THERMAL_CLUSTER_TABLE,
    THERMAL_CO2_COST_TABLE,
    THERMAL_FUEL_COST_TABLE,
    THERMAL_MODULATION_TABLE,
    THERMAL_PREPRO_TABLE,
    THERMAL_SERIES_TABLE,
)
from antarest.study.dao.database.sql_utils import upsert_multiple, upsert_one

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


def _normalize_thermal_id(thermal_id: str) -> str:
    return thermal_id.lower()


def _normalize_group(group: Any) -> Any:
    return group.value if hasattr(group, "value") else group


class DatabaseThermalDao(ThermalDao):
    """
    Database implementation of ThermalDao.
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

    def get_study_id(self) -> str:
        """Get the study ID for database queries."""
        return self._study_id

    def get_session(self) -> Session:
        """Get the SQLAlchemy session for database operations."""
        return self._db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    def _convert_db_row_to_thermal(self, row: Any) -> ThermalCluster:
        cluster = ThermalCluster(
            id=row.thermal_id,
            name=row.name,
            unit_count=row.unit_count,
            nominal_capacity=row.nominal_capacity,
            enabled=row.enabled,
            group=row.group,
            gen_ts=row.gen_ts,
            min_stable_power=row.min_stable_power,
            min_up_time=row.min_up_time,
            min_down_time=row.min_down_time,
            must_run=row.must_run,
            spinning=row.spinning,
            volatility_forced=row.volatility_forced,
            volatility_planned=row.volatility_planned,
            law_forced=row.law_forced,
            law_planned=row.law_planned,
            marginal_cost=row.marginal_cost,
            spread_cost=row.spread_cost,
            fixed_cost=row.fixed_cost,
            startup_cost=row.startup_cost,
            market_bid_cost=row.market_bid_cost,
            co2=row.co2,
            nh3=row.nh3,
            so2=row.so2,
            nox=row.nox,
            pm2_5=row.pm2_5,
            pm5=row.pm5,
            pm10=row.pm10,
            nmvoc=row.nmvoc,
            op1=row.op1,
            op2=row.op2,
            op3=row.op3,
            op4=row.op4,
            op5=row.op5,
            cost_generation=row.cost_generation,
            efficiency=row.efficiency,
            variable_o_m_cost=row.variable_o_m_cost,
        )
        version = self.get_impl().get_version()
        validate_thermal_cluster_against_version(version, cluster)
        initialize_thermal_cluster(cluster, version)
        return cluster

    def _convert_thermal_cluster_to_row(self, area_id: str, cluster: ThermalCluster) -> dict[str, Any]:
        return dict(
            study_id=self.get_study_id(),
            area_id=area_id,
            thermal_id=_normalize_thermal_id(cluster.id),
            name=cluster.name,
            unit_count=cluster.unit_count,
            nominal_capacity=cluster.nominal_capacity,
            enabled=cluster.enabled,
            group=_normalize_group(cluster.group),
            gen_ts=cluster.gen_ts,
            min_stable_power=cluster.min_stable_power,
            min_up_time=cluster.min_up_time,
            min_down_time=cluster.min_down_time,
            must_run=cluster.must_run,
            spinning=cluster.spinning,
            volatility_forced=cluster.volatility_forced,
            volatility_planned=cluster.volatility_planned,
            law_forced=cluster.law_forced,
            law_planned=cluster.law_planned,
            marginal_cost=cluster.marginal_cost,
            spread_cost=cluster.spread_cost,
            fixed_cost=cluster.fixed_cost,
            startup_cost=cluster.startup_cost,
            market_bid_cost=cluster.market_bid_cost,
            co2=cluster.co2,
            nh3=cluster.nh3,
            so2=cluster.so2,
            nox=cluster.nox,
            pm2_5=cluster.pm2_5,
            pm5=cluster.pm5,
            pm10=cluster.pm10,
            nmvoc=cluster.nmvoc,
            op1=cluster.op1,
            op2=cluster.op2,
            op3=cluster.op3,
            op4=cluster.op4,
            op5=cluster.op5,
            cost_generation=cluster.cost_generation,
            efficiency=cluster.efficiency,
            variable_o_m_cost=cluster.variable_o_m_cost,
        )

    def _get_thermal_matrix_row(self, area_id: str, thermal_id: str, table: Table) -> Row[Any] | None:
        study_id = self.get_study_id()
        session = self.get_session()
        stmt = select(table).where(
            (table.c.study_id == study_id)
            & (table.c.area_id == area_id)
            & (table.c.thermal_id == _normalize_thermal_id(thermal_id))
        )
        return session.execute(stmt).fetchone()

    def _get_thermal_matrix(self, area_id: str, thermal_id: str, table: Table) -> pl.DataFrame:
        row = self._get_thermal_matrix_row(area_id, thermal_id, table)
        if not row:
            raise ThermalClusterNotFound(area_id, thermal_id)
        return self.get_impl().get_matrix(row.matrix_id)

    def _save_thermal_matrix(self, area_id: str, thermal_id: str, table: Table, matrix_id: str) -> None:
        study_id = self.get_study_id()
        session = self.get_session()
        thermal_id = _normalize_thermal_id(thermal_id)

        if not self.thermal_exists(area_id, thermal_id):
            raise ThermalClusterNotFound(area_id, thermal_id)

        row = self._get_thermal_matrix_row(area_id, thermal_id, table)
        if not row:
            stmt_insert = insert(table).values(
                study_id=study_id, area_id=area_id, thermal_id=thermal_id, matrix_id=matrix_id
            )
            session.execute(stmt_insert)
        else:
            stmt_update = (
                update(table)
                .where(
                    (table.c.study_id == study_id) & (table.c.area_id == area_id) & (table.c.thermal_id == thermal_id)
                )
                .values(matrix_id=matrix_id)
            )
            session.execute(stmt_update)
        session.commit()

    @override
    def save_thermal(self, area_id: str, thermal: ThermalCluster) -> None:
        study_id = self.get_study_id()
        session = self.get_session()

        validate_area_exists(session, study_id, area_id)
        values = self._convert_thermal_cluster_to_row(area_id, thermal)
        upsert_one(session, THERMAL_CLUSTER_TABLE, values)
        session.commit()

    @override
    def save_thermals(self, area_id: str, thermals: Sequence[ThermalCluster]) -> None:
        if not thermals:
            return

        session = self.get_session()
        study_id = self.get_study_id()
        validate_area_exists(session, study_id, area_id)

        values = [self._convert_thermal_cluster_to_row(area_id, thermal) for thermal in thermals]

        upsert_multiple(
            session=session,
            table=THERMAL_CLUSTER_TABLE,
            values=values,
        )
        session.commit()

    @override
    def save_thermal_prepro(self, area_id: str, thermal_id: str, series_id: str) -> None:
        self._save_thermal_matrix(area_id, thermal_id, THERMAL_PREPRO_TABLE, series_id)

    @override
    def save_thermal_modulation(self, area_id: str, thermal_id: str, series_id: str) -> None:
        self._save_thermal_matrix(area_id, thermal_id, THERMAL_MODULATION_TABLE, series_id)

    @override
    def save_thermal_series(self, area_id: str, thermal_id: str, series_id: str) -> None:
        self._save_thermal_matrix(area_id, thermal_id, THERMAL_SERIES_TABLE, series_id)

    @override
    def save_thermal_fuel_cost(self, area_id: str, thermal_id: str, series_id: str) -> None:
        self._save_thermal_matrix(area_id, thermal_id, THERMAL_FUEL_COST_TABLE, series_id)

    @override
    def save_thermal_co2_cost(self, area_id: str, thermal_id: str, series_id: str) -> None:
        self._save_thermal_matrix(area_id, thermal_id, THERMAL_CO2_COST_TABLE, series_id)

    @override
    def delete_thermal(self, area_id: str, thermal: ThermalCluster) -> None:
        study_id = self.get_study_id()
        session = self.get_session()
        thermal_id = _normalize_thermal_id(thermal.id)

        if not self.thermal_exists(area_id, thermal_id):
            raise ThermalClusterNotFound(area_id, thermal_id)

        session.execute(
            delete(THERMAL_CLUSTER_TABLE).where(
                (THERMAL_CLUSTER_TABLE.c.study_id == study_id)
                & (THERMAL_CLUSTER_TABLE.c.area_id == area_id)
                & (THERMAL_CLUSTER_TABLE.c.thermal_id == thermal_id)
            )
        )
        session.commit()

    @override
    def get_all_thermals(self) -> dict[str, dict[str, ThermalCluster]]:
        study_id = self.get_study_id()
        session = self.get_session()

        stmt = select(THERMAL_CLUSTER_TABLE).where(THERMAL_CLUSTER_TABLE.c.study_id == study_id)
        rows = session.execute(stmt).fetchall()

        thermals_by_areas: dict[str, dict[str, ThermalCluster]] = {}
        for row in rows:
            thermal = self._convert_db_row_to_thermal(row)
            thermals_by_areas.setdefault(row.area_id, {})[thermal.id.lower()] = thermal
        return thermals_by_areas

    @override
    def get_all_thermals_for_area(self, area_id: str) -> Sequence[ThermalCluster]:
        study_id = self.get_study_id()
        session = self.get_session()
        validate_area_exists(session, study_id, area_id)

        stmt = select(THERMAL_CLUSTER_TABLE).where(
            (THERMAL_CLUSTER_TABLE.c.study_id == study_id) & (THERMAL_CLUSTER_TABLE.c.area_id == area_id)
        )
        rows = session.execute(stmt).fetchall()
        return [self._convert_db_row_to_thermal(row) for row in rows]

    @override
    def get_thermal(self, area_id: str, thermal_id: str) -> ThermalCluster:
        study_id = self.get_study_id()
        session = self.get_session()
        thermal_id = _normalize_thermal_id(thermal_id)

        stmt = select(THERMAL_CLUSTER_TABLE).where(
            (THERMAL_CLUSTER_TABLE.c.study_id == study_id)
            & (THERMAL_CLUSTER_TABLE.c.area_id == area_id)
            & (THERMAL_CLUSTER_TABLE.c.thermal_id == thermal_id)
        )
        row = session.execute(stmt).fetchone()
        if not row:
            raise ThermalClusterNotFound(area_id, thermal_id)

        return self._convert_db_row_to_thermal(row)

    @override
    def thermal_exists(self, area_id: str, thermal_id: str) -> bool:
        study_id = self.get_study_id()
        session = self.get_session()
        thermal_id = _normalize_thermal_id(thermal_id)

        stmt = select(THERMAL_CLUSTER_TABLE.c.thermal_id).where(
            (THERMAL_CLUSTER_TABLE.c.study_id == study_id)
            & (THERMAL_CLUSTER_TABLE.c.area_id == area_id)
            & (THERMAL_CLUSTER_TABLE.c.thermal_id == thermal_id)
        )
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
