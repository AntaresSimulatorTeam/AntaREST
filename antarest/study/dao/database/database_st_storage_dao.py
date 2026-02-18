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
Database implementation of StStorageDao.
"""

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Sequence

import polars as pl
from sqlalchemy import Row, Table, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import STStorageAdditionalConstraintNotFound, STStorageNotFound
from antarest.study.business.model.sts_model import (
    STStorage,
    STStorageAdditionalConstraint,
    STStorageAdditionalConstraintsMap,
)
from antarest.study.dao.api.st_storage_dao import STStorageDao
from antarest.study.dao.database.models.st_storage import (
    COST_INJECTION_TABLE,
    COST_LEVEL_TABLE,
    COST_VARIATION_INJECTION_TABLE,
    COST_VARIATION_WITHDRAWAL_TABLE,
    COST_WITHDRAWAL_TABLE,
    INFLOWS_TABLE,
    LOWER_RULE_CURVE_TABLE,
    PMAX_INJECTION_TABLE,
    PMAX_WITHDRAWAL_TABLE,
    ST_STORAGE_ADDITIONAL_CONSTRAINT_MATRIX_TABLE,
    ST_STORAGE_ADDITIONAL_CONSTRAINT_TABLE,
    ST_STORAGE_TABLE,
    UPPER_RULE_CURVE_TABLE,
)
from antarest.study.dao.database.sql_utils import upsert_multiple, upsert_one

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


class DatabaseStStorageDao(STStorageDao):
    """
    Database implementation of StStorageDao.
    """

    def __init__(self, study_id: str, db_session: Session) -> None:
        """
        Initialize DatabaseStStorageDao with dependencies.

        Args:
            study_id: The study ID for database queries.
            db_session: SQLAlchemy session for database operations.
        """
        self._study_id = study_id
        self._db_session = db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    def _convert_st_storage_to_db_values(self, area_id: str, st_storage: STStorage) -> dict[str, Any]:
        values = dict(study_id=self._study_id, area_id=area_id, **st_storage.model_dump())
        values["st_storage_id"] = values.pop("id")
        return values

    def _convert_db_values_to_st_storage(self, row: Row[Any]) -> STStorage:
        data = {k: v for k, v in row._mapping.items() if k not in {"study_id", "area_id"}}
        data["id"] = data.pop("st_storage_id")
        return STStorage(**data)

    def _convert_constraint_to_db_values(
        self, area_id: str, storage_id: str, constraint: STStorageAdditionalConstraint
    ) -> dict[str, Any]:
        values = dict(study_id=self._study_id, area_id=area_id, st_storage_id=storage_id, **constraint.model_dump())
        values["constraint_id"] = values.pop("id")
        return values

    def _convert_db_values_to_constraint(self, row: Row[Any]) -> STStorageAdditionalConstraint:
        data = {k: v for k, v in row._mapping.items() if k not in {"study_id", "area_id", "st_storage_id"}}
        data["id"] = data.pop("constraint_id")
        return STStorageAdditionalConstraint(**data)

    @override
    def save_st_storage(self, area_id: str, st_storage: STStorage) -> None:
        session = self._db_session

        value = self._convert_st_storage_to_db_values(area_id, st_storage)

        try:
            upsert_one(session, ST_STORAGE_TABLE, value)
        except IntegrityError as e:
            raise STStorageNotFound(area_id, st_storage.id) from e

        session.commit()

    @override
    def save_st_storages(self, area_id: str, storages: Sequence[STStorage]) -> None:
        session = self._db_session

        values = [self._convert_st_storage_to_db_values(area_id, st_storage) for st_storage in storages]

        try:
            upsert_multiple(session, ST_STORAGE_TABLE, values)
        except IntegrityError as e:
            raise STStorageNotFound(area_id, storages[0].id) from e

        session.commit()

    @override
    def get_all_st_storages(self) -> dict[str, dict[str, STStorage]]:
        session, study_id = self._db_session, self._study_id

        stmt = select(ST_STORAGE_TABLE).where(ST_STORAGE_TABLE.c.study_id == study_id)
        rows = session.execute(stmt).fetchall()

        st_storages_by_areas: dict[str, dict[str, STStorage]] = {}
        for row in rows:
            st_storage = self._convert_db_values_to_st_storage(row)
            st_storages_by_areas.setdefault(row.area_id, {})[st_storage.id.lower()] = st_storage
        return st_storages_by_areas

    @override
    def get_all_st_storages_for_area(self, area_id: str) -> Sequence[STStorage]:
        session, study_id = self._db_session, self._study_id

        stmt = select(ST_STORAGE_TABLE).where(
            (ST_STORAGE_TABLE.c.study_id == study_id) & (ST_STORAGE_TABLE.c.area_id == area_id)
        )

        rows = session.execute(stmt).fetchall()

        return [self._convert_db_values_to_st_storage(row) for row in rows]

    @override
    def get_st_storage(self, area_id: str, storage_id: str) -> STStorage:
        session, study_id = self._db_session, self._study_id

        stmt = select(ST_STORAGE_TABLE).where(
            (ST_STORAGE_TABLE.c.study_id == study_id)
            & (ST_STORAGE_TABLE.c.area_id == area_id)
            & (ST_STORAGE_TABLE.c.st_storage_id == storage_id)
        )

        row = session.execute(stmt).fetchone()

        if not row:
            raise STStorageNotFound(area_id, storage_id)

        return self._convert_db_values_to_st_storage(row)

    @override
    def st_storage_exists(self, area_id: str, storage_id: str) -> bool:
        session, study_id = self._db_session, self._study_id

        stmt = select(ST_STORAGE_TABLE).where(
            (ST_STORAGE_TABLE.c.study_id == study_id)
            & (ST_STORAGE_TABLE.c.area_id == area_id)
            & (ST_STORAGE_TABLE.c.st_storage_id == storage_id)
        )

        return session.execute(stmt).fetchone() is not None

    @override
    def delete_st_storage(self, area_id: str, storage: STStorage) -> None:
        session = self._db_session

        if not self.st_storage_exists(area_id, storage.id):
            raise STStorageNotFound(area_id, storage.id)

        session.execute(
            ST_STORAGE_TABLE.delete().where(
                (ST_STORAGE_TABLE.c.study_id == self._study_id)
                & (ST_STORAGE_TABLE.c.area_id == area_id)
                & (ST_STORAGE_TABLE.c.st_storage_id == storage.id)
            )
        )
        session.commit()

    @override
    def save_st_storage_additional_constraints(
        self, area_id: str, storage_id: str, constraints: list[STStorageAdditionalConstraint]
    ) -> None:
        session = self._db_session

        values = [self._convert_constraint_to_db_values(area_id, storage_id, constraint) for constraint in constraints]

        try:
            upsert_multiple(session, ST_STORAGE_ADDITIONAL_CONSTRAINT_TABLE, values)
        except IntegrityError as e:
            raise STStorageNotFound(area_id, storage_id) from e

        session.commit()

    @override
    def get_all_st_storage_additional_constraints(self) -> STStorageAdditionalConstraintsMap:
        session, study_id = self._db_session, self._study_id

        stmt = select(ST_STORAGE_ADDITIONAL_CONSTRAINT_TABLE).where(
            ST_STORAGE_ADDITIONAL_CONSTRAINT_TABLE.c.study_id == study_id
        )
        rows = session.execute(stmt).fetchall()

        constraint_by_areas: STStorageAdditionalConstraintsMap = {}
        for row in rows:
            constraint = self._convert_db_values_to_constraint(row)
            constraint_by_areas.setdefault(row.area_id, {}).setdefault(row.st_storage_id.lower(), []).append(constraint)
        return constraint_by_areas

    @override
    def get_st_storage_additional_constraints(
        self, area_id: str, storage_id: str
    ) -> list[STStorageAdditionalConstraint]:
        session, study_id = self._db_session, self._study_id

        table = ST_STORAGE_ADDITIONAL_CONSTRAINT_TABLE
        stmt = select(table).where(
            (table.c.study_id == study_id) & (table.c.area_id == area_id) & (table.c.st_storage_id == storage_id)
        )
        rows = session.execute(stmt).fetchall()

        return [self._convert_db_values_to_constraint(row) for row in rows]

    @override
    def delete_st_storage_additional_constraints(self, area_id: str, storage_id: str, constraints: list[str]) -> None:
        session = self._db_session
        table = ST_STORAGE_ADDITIONAL_CONSTRAINT_TABLE

        session.execute(
            table.delete().where(
                (table.c.study_id == self._study_id)
                & (table.c.area_id == area_id)
                & (table.c.st_storage_id == storage_id)
                & (table.c.constraint_id.in_(constraints))
            )
        )
        session.commit()

    @override
    def save_st_storage_pmax_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._save_st_storage_matrix(area_id, storage_id, PMAX_INJECTION_TABLE, series_id)

    @override
    def save_st_storage_pmax_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._save_st_storage_matrix(area_id, storage_id, PMAX_WITHDRAWAL_TABLE, series_id)

    @override
    def save_st_storage_lower_rule_curve(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._save_st_storage_matrix(area_id, storage_id, LOWER_RULE_CURVE_TABLE, series_id)

    @override
    def save_st_storage_upper_rule_curve(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._save_st_storage_matrix(area_id, storage_id, UPPER_RULE_CURVE_TABLE, series_id)

    @override
    def save_st_storage_inflows(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._save_st_storage_matrix(area_id, storage_id, INFLOWS_TABLE, series_id)

    @override
    def save_st_storage_cost_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._save_st_storage_matrix(area_id, storage_id, COST_INJECTION_TABLE, series_id)

    @override
    def save_st_storage_cost_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._save_st_storage_matrix(area_id, storage_id, COST_WITHDRAWAL_TABLE, series_id)

    @override
    def save_st_storage_cost_level(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._save_st_storage_matrix(area_id, storage_id, COST_LEVEL_TABLE, series_id)

    @override
    def save_st_storage_cost_variation_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._save_st_storage_matrix(area_id, storage_id, COST_VARIATION_INJECTION_TABLE, series_id)

    @override
    def save_st_storage_cost_variation_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._save_st_storage_matrix(area_id, storage_id, COST_VARIATION_WITHDRAWAL_TABLE, series_id)

    @override
    def get_st_storage_pmax_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._get_st_storage_matrix(area_id, storage_id, PMAX_WITHDRAWAL_TABLE)

    @override
    def get_st_storage_pmax_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._get_st_storage_matrix(area_id, storage_id, PMAX_INJECTION_TABLE)

    @override
    def get_st_storage_lower_rule_curve(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._get_st_storage_matrix(area_id, storage_id, LOWER_RULE_CURVE_TABLE)

    @override
    def get_st_storage_upper_rule_curve(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._get_st_storage_matrix(area_id, storage_id, UPPER_RULE_CURVE_TABLE)

    @override
    def get_st_storage_inflows(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._get_st_storage_matrix(area_id, storage_id, INFLOWS_TABLE)

    @override
    def get_st_storage_cost_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._get_st_storage_matrix(area_id, storage_id, COST_INJECTION_TABLE)

    @override
    def get_st_storage_cost_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._get_st_storage_matrix(area_id, storage_id, COST_WITHDRAWAL_TABLE)

    @override
    def get_st_storage_cost_level(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._get_st_storage_matrix(area_id, storage_id, COST_LEVEL_TABLE)

    @override
    def get_st_storage_cost_variation_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._get_st_storage_matrix(area_id, storage_id, COST_VARIATION_INJECTION_TABLE)

    @override
    def get_st_storage_cost_variation_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._get_st_storage_matrix(area_id, storage_id, COST_VARIATION_WITHDRAWAL_TABLE)

    @override
    def save_st_storage_constraint_matrix(
        self, area_id: str, storage_id: str, constraint_id: str, series_id: str
    ) -> None:
        try:
            values = {
                "study_id": self._study_id,
                "area_id": area_id,
                "st_storage_id": storage_id,
                "constraint_id": constraint_id,
                "matrix_id": series_id,
            }
            upsert_one(self._db_session, ST_STORAGE_ADDITIONAL_CONSTRAINT_MATRIX_TABLE, values)
        except IntegrityError as e:
            raise STStorageAdditionalConstraintNotFound(area_id, constraint_id) from e

        self._db_session.commit()

    @override
    def get_st_storage_additional_constraints_matrix(
        self, area_id: str, storage_id: str, constraint_id: str
    ) -> pl.DataFrame:
        table = ST_STORAGE_ADDITIONAL_CONSTRAINT_MATRIX_TABLE
        stmt = select(table).where(
            (table.c.study_id == self._study_id)
            & (table.c.area_id == area_id)
            & (table.c.st_storage_id == storage_id)
            & (table.c.constraint_id == constraint_id)
        )
        row = self._db_session.execute(stmt).fetchone()
        if not row:
            raise STStorageAdditionalConstraintNotFound(area_id, constraint_id)
        return self.get_impl().get_matrix(row.matrix_id)

    def _save_st_storage_matrix(self, area_id: str, storage_id: str, table: Table, matrix_id: str) -> None:
        try:
            values = {
                "study_id": self._study_id,
                "area_id": area_id,
                "st_storage_id": storage_id,
                "matrix_id": matrix_id,
            }
            upsert_one(self._db_session, table, values)
        except IntegrityError as e:
            raise STStorageNotFound(area_id, storage_id) from e

        self._db_session.commit()

    def _get_st_storage_matrix_row(self, area_id: str, storage_id: str, table: Table) -> Row[Any] | None:
        stmt = select(table).where(
            (table.c.study_id == self._study_id) & (table.c.area_id == area_id) & (table.c.st_storage_id == storage_id)
        )
        return self._db_session.execute(stmt).fetchone()

    def _get_st_storage_matrix(self, area_id: str, storage_id: str, table: Table) -> pl.DataFrame:
        row = self._get_st_storage_matrix_row(area_id, storage_id, table)
        if not row:
            raise STStorageNotFound(area_id, storage_id)
        return self.get_impl().get_matrix(row.matrix_id)
