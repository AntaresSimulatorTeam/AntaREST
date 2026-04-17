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
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, NoReturn

import polars as pl
from sqlalchemy import CursorResult, Row, Table, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import (
    AreaNotFound,
    STStorageAdditionalConstraintNotFound,
    STStorageNotFound,
    STStoragesNotFound,
)
from antarest.study.business.model.sts_model import (
    STStorage,
    STStorageAdditionalConstraint,
    STStorageAdditionalConstraintsMap,
    initialize_st_storage,
    validate_st_storage_against_version,
)
from antarest.study.dao.api.st_storage_dao import STStorageDao
from antarest.study.dao.common import (
    AreaId,
    SeriesId,
    StStorageConstraintSeriesMapping,
    StStorageId,
    StStorageSeriesMapping,
)
from antarest.study.dao.database.common import get_row_representation_as_dict, validate_area_exists
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
from antarest.study.dao.database.sql_utils import upsert_multiple
from antarest.study.storage.rawstudy.model.filesystem.matrix.simulator_default import (
    default_cost_level,
    default_scenario_hourly,
    default_scenario_hourly_ones,
)

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

    def _convert_st_storage_to_row(self, area_id: str, st_storage: STStorage) -> dict[str, Any]:
        values = dict(study_id=self._study_id, area_id=area_id, **st_storage.model_dump())
        values["st_storage_id"] = values.pop("id")
        return values

    def _convert_db_row_to_st_storage(self, row: Row[Any]) -> STStorage:
        data = get_row_representation_as_dict(row)
        del data["study_id"]
        del data["area_id"]
        data["id"] = data.pop("st_storage_id")
        storage = STStorage(**data)
        version = self.get_impl().get_version()
        validate_st_storage_against_version(version, storage)
        initialize_st_storage(storage, version)
        return storage

    def _convert_constraint_to_row(
        self, area_id: str, storage_id: str, constraint: STStorageAdditionalConstraint
    ) -> dict[str, Any]:
        values = dict(study_id=self._study_id, area_id=area_id, st_storage_id=storage_id, **constraint.model_dump())
        values["constraint_id"] = values.pop("id")
        return values

    def _convert_db_row_to_constraint(self, row: Row[Any]) -> STStorageAdditionalConstraint:
        data = get_row_representation_as_dict(row)
        del data["study_id"]
        del data["area_id"]
        del data["st_storage_id"]
        data["id"] = data.pop("constraint_id")
        return STStorageAdditionalConstraint(**data)

    def _raise_the_right_exc(self, data: dict[AreaId, list[StStorageId]], exc: IntegrityError | None = None) -> None:
        # Checks if some areas are missing
        existing_ids = set(self.get_impl().get_all_area_ids())
        if invalid_areas := set(data) - existing_ids:
            raise AreaNotFound(*invalid_areas)

        # Means the issue lies in the short-term storages
        all_existing_storages = self.get_all_st_storages()
        invalid_sts_dict = {}
        for area_id, value in data.items():
            if invalid_sts := set(data[area_id]) - set(all_existing_storages.get(area_id, [])):
                invalid_sts_dict[area_id] = invalid_sts

        if len(invalid_sts_dict) == 1 and len(list(invalid_sts_dict.values())[0]) == 1:
            # Only one short-term storage is missing, keep the clearer exception
            area_id = next(iter(invalid_sts_dict))
            raise STStorageNotFound(area_id, next(iter(invalid_sts_dict[area_id]))) from exc

        elif invalid_sts_dict:
            raise STStoragesNotFound(invalid_sts_dict) from exc

    def _raise_the_right_storage_exception(
        self, data: dict[AreaId, list[StStorageId]], exc: IntegrityError | None = None
    ) -> NoReturn:
        self._raise_the_right_exc(data, exc)

        # All short-term storages exist. It means that the DB table does not contain the information.
        raise ValueError("One of the short-term storages table is not filled as it should") from exc

    def _raise_the_right_constraint_exception(
        self, data: dict[AreaId, dict[StStorageId, str]], exc: IntegrityError | None = None
    ) -> NoReturn:
        sts_data = {area_id: list(storage_ids) for area_id, storage_ids in data.items()}
        self._raise_the_right_exc(sts_data, exc)

        # Means the issue lies in the additional constraints
        constraints_dict = self.get_all_st_storage_additional_constraints()
        for area_id, sts_dict in data.items():
            for sts_id in sts_dict:
                existing_ids = {c.id for c in constraints_dict.get(area_id, {}).get(sts_id, [])}
                for constraint_id in sts_dict[sts_id]:
                    if constraint_id not in existing_ids:
                        raise STStorageAdditionalConstraintNotFound(area_id, constraint_id) from exc

        # All constraints exist. It means that the DB table does not contain the information.
        raise ValueError("One of the short-term storages constraints table is not filled as it should") from exc

    @override
    def save_st_storages(self, data: dict[AreaId, list[STStorage]]) -> None:
        if not data:
            return

        values = []
        for area_id, storages in data.items():
            for storage in storages:
                values.append(self._convert_st_storage_to_row(area_id, storage))

        session = self._db_session
        try:
            upsert_multiple(session, ST_STORAGE_TABLE, values)
        except IntegrityError as e:
            # Means an area does not exist
            invalid_areas = self.get_impl().get_invalid_area_ids(list(data))
            raise AreaNotFound(*invalid_areas) from e

        session.commit()

    @override
    def get_all_st_storages(self) -> dict[str, dict[str, STStorage]]:
        session, study_id = self._db_session, self._study_id

        stmt = select(ST_STORAGE_TABLE).where(ST_STORAGE_TABLE.c.study_id == study_id)
        rows = session.execute(stmt).fetchall()

        st_storages_by_areas: dict[str, dict[str, STStorage]] = {}
        for row in rows:
            st_storage = self._convert_db_row_to_st_storage(row)
            st_storages_by_areas.setdefault(row.area_id, {})[st_storage.id] = st_storage
        return st_storages_by_areas

    @override
    def get_all_st_storages_for_area(self, area_id: str) -> Sequence[STStorage]:
        session, study_id = self._db_session, self._study_id

        stmt = select(ST_STORAGE_TABLE).where(
            (ST_STORAGE_TABLE.c.study_id == study_id) & (ST_STORAGE_TABLE.c.area_id == area_id)
        )

        rows = session.execute(stmt).fetchall()

        if not rows:
            validate_area_exists(session, study_id, area_id)

        return [self._convert_db_row_to_st_storage(row) for row in rows]

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
            self._raise_the_right_storage_exception({area_id: [storage_id]})

        return self._convert_db_row_to_st_storage(row)

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

        result = session.execute(
            ST_STORAGE_TABLE.delete().where(
                (ST_STORAGE_TABLE.c.study_id == self._study_id)
                & (ST_STORAGE_TABLE.c.area_id == area_id)
                & (ST_STORAGE_TABLE.c.st_storage_id == storage.id)
            )
        )

        assert isinstance(result, CursorResult)
        if result.rowcount == 0:
            self._raise_the_right_storage_exception({area_id: [storage.id]})

        session.commit()

    @override
    def save_st_storage_additional_constraints(
        self, data: dict[AreaId, dict[StStorageId, list[STStorageAdditionalConstraint]]]
    ) -> None:
        session = self._db_session

        values = []
        for area_id, value in data.items():
            for storage_id, constraints in value.items():
                for constraint in constraints:
                    values.append(self._convert_constraint_to_row(area_id, storage_id, constraint))

        try:
            upsert_multiple(session, ST_STORAGE_ADDITIONAL_CONSTRAINT_TABLE, values)
        except IntegrityError as e:
            invalid_data = {
                area_id: {sts_id: constraint.id for sts_id, constraints in v.items() for constraint in constraints}
                for area_id, v in data.items()
            }
            self._raise_the_right_constraint_exception(invalid_data, e)

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
            constraint = self._convert_db_row_to_constraint(row)
            constraint_by_areas.setdefault(row.area_id, {}).setdefault(row.st_storage_id, []).append(constraint)
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

        return [self._convert_db_row_to_constraint(row) for row in rows]

    @override
    def delete_st_storage_additional_constraints(self, area_id: str, storage_id: str, constraints: list[str]) -> None:
        session = self._db_session
        table = ST_STORAGE_ADDITIONAL_CONSTRAINT_TABLE

        result = session.execute(
            table.delete().where(
                (table.c.study_id == self._study_id)
                & (table.c.area_id == area_id)
                & (table.c.st_storage_id == storage_id)
                & (table.c.constraint_id.in_(constraints))
            )
        )

        assert isinstance(result, CursorResult)
        if result.rowcount == 0:
            self._raise_the_right_storage_exception({area_id: [storage_id]})

        session.commit()

    def _save_st_storage_matrix(self, series: StStorageSeriesMapping, table: Table) -> None:
        study_id = self._study_id
        session = self._db_session

        try:
            values = []
            for area_id, value in series.items():
                for sts_id, matrix_id in value.items():
                    data = {"study_id": study_id, "area_id": area_id, "st_storage_id": sts_id, "matrix_id": matrix_id}
                    values.append(data)
            upsert_multiple(session, table, values)
        except IntegrityError as e:
            invalid_data = {area_id: list(st_storage_dict) for area_id, st_storage_dict in series.items()}
            self._raise_the_right_storage_exception(invalid_data, e)

        session.commit()

    @override
    def save_st_storage_pmax_injection(self, series: StStorageSeriesMapping) -> None:
        self._save_st_storage_matrix(series, PMAX_INJECTION_TABLE)

    @override
    def save_st_storage_pmax_withdrawal(self, series: StStorageSeriesMapping) -> None:
        self._save_st_storage_matrix(series, PMAX_WITHDRAWAL_TABLE)

    @override
    def save_st_storage_lower_rule_curve(self, series: StStorageSeriesMapping) -> None:
        self._save_st_storage_matrix(series, LOWER_RULE_CURVE_TABLE)

    @override
    def save_st_storage_upper_rule_curve(self, series: StStorageSeriesMapping) -> None:
        self._save_st_storage_matrix(series, UPPER_RULE_CURVE_TABLE)

    @override
    def save_st_storage_inflows(self, series: StStorageSeriesMapping) -> None:
        self._save_st_storage_matrix(series, INFLOWS_TABLE)

    @override
    def save_st_storage_cost_injection(self, series: StStorageSeriesMapping) -> None:
        self._save_st_storage_matrix(series, COST_INJECTION_TABLE)

    @override
    def save_st_storage_cost_withdrawal(self, series: StStorageSeriesMapping) -> None:
        self._save_st_storage_matrix(series, COST_WITHDRAWAL_TABLE)

    @override
    def save_st_storage_cost_level(self, series: StStorageSeriesMapping) -> None:
        self._save_st_storage_matrix(series, COST_LEVEL_TABLE)

    @override
    def save_st_storage_cost_variation_injection(self, series: StStorageSeriesMapping) -> None:
        self._save_st_storage_matrix(series, COST_VARIATION_INJECTION_TABLE)

    @override
    def save_st_storage_cost_variation_withdrawal(self, series: StStorageSeriesMapping) -> None:
        self._save_st_storage_matrix(series, COST_VARIATION_WITHDRAWAL_TABLE)

    @override
    def get_st_storage_pmax_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._get_st_storage_matrix(area_id, storage_id, PMAX_WITHDRAWAL_TABLE)
        return self.get_impl().get_matrix(matrix_id, default_empty_supplier=default_scenario_hourly_ones)

    @override
    def get_st_storage_pmax_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._get_st_storage_matrix(area_id, storage_id, PMAX_INJECTION_TABLE)
        return self.get_impl().get_matrix(matrix_id, default_empty_supplier=default_scenario_hourly_ones)

    @override
    def get_st_storage_lower_rule_curve(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._get_st_storage_matrix(area_id, storage_id, LOWER_RULE_CURVE_TABLE)
        return self.get_impl().get_matrix(matrix_id, default_empty_supplier=default_scenario_hourly)

    @override
    def get_st_storage_upper_rule_curve(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._get_st_storage_matrix(area_id, storage_id, UPPER_RULE_CURVE_TABLE)
        return self.get_impl().get_matrix(matrix_id, default_empty_supplier=default_scenario_hourly_ones)

    @override
    def get_st_storage_inflows(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._get_st_storage_matrix(area_id, storage_id, INFLOWS_TABLE)
        return self.get_impl().get_matrix(matrix_id, default_empty_supplier=default_scenario_hourly)

    @override
    def get_st_storage_cost_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._get_st_storage_matrix(area_id, storage_id, COST_INJECTION_TABLE)
        return self.get_impl().get_matrix(matrix_id, default_empty_supplier=default_scenario_hourly)

    @override
    def get_st_storage_cost_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._get_st_storage_matrix(area_id, storage_id, COST_WITHDRAWAL_TABLE)
        return self.get_impl().get_matrix(matrix_id, default_empty_supplier=default_scenario_hourly)

    @override
    def get_st_storage_cost_level(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._get_st_storage_matrix(area_id, storage_id, COST_LEVEL_TABLE)
        return self.get_impl().get_matrix(matrix_id, default_empty_supplier=default_cost_level)

    @override
    def get_st_storage_cost_variation_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._get_st_storage_matrix(area_id, storage_id, COST_VARIATION_INJECTION_TABLE)
        return self.get_impl().get_matrix(matrix_id, default_empty_supplier=default_scenario_hourly)

    @override
    def get_st_storage_cost_variation_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._get_st_storage_matrix(area_id, storage_id, COST_VARIATION_WITHDRAWAL_TABLE)
        return self.get_impl().get_matrix(matrix_id, default_empty_supplier=default_scenario_hourly)

    def _get_all_sts_matrix(self, table: Table) -> StStorageSeriesMapping:
        study_id = self._study_id
        session = self._db_session
        stmt = select(table).where(table.c.study_id == study_id)
        rows = session.execute(stmt).fetchall()
        result: StStorageSeriesMapping = {}
        for row in rows:
            result.setdefault(row.area_id, {})[row.st_storage_id] = row.matrix_id
        return result

    @override
    def get_all_st_storage_pmax_injection(self) -> StStorageSeriesMapping:
        return self._get_all_sts_matrix(PMAX_INJECTION_TABLE)

    @override
    def get_all_st_storage_pmax_withdrawal(self) -> StStorageSeriesMapping:
        return self._get_all_sts_matrix(PMAX_WITHDRAWAL_TABLE)

    @override
    def get_all_st_storage_lower_rule_curve(self) -> StStorageSeriesMapping:
        return self._get_all_sts_matrix(LOWER_RULE_CURVE_TABLE)

    @override
    def get_all_st_storage_upper_rule_curve(self) -> StStorageSeriesMapping:
        return self._get_all_sts_matrix(UPPER_RULE_CURVE_TABLE)

    @override
    def get_all_st_storage_inflows(self) -> StStorageSeriesMapping:
        return self._get_all_sts_matrix(INFLOWS_TABLE)

    @override
    def get_all_st_storage_cost_injection(self) -> StStorageSeriesMapping:
        return self._get_all_sts_matrix(COST_INJECTION_TABLE)

    @override
    def get_all_st_storage_cost_withdrawal(self) -> StStorageSeriesMapping:
        return self._get_all_sts_matrix(COST_WITHDRAWAL_TABLE)

    @override
    def get_all_st_storage_cost_level(self) -> StStorageSeriesMapping:
        return self._get_all_sts_matrix(COST_LEVEL_TABLE)

    @override
    def get_all_st_storage_cost_variation_injection(self) -> StStorageSeriesMapping:
        return self._get_all_sts_matrix(COST_VARIATION_INJECTION_TABLE)

    @override
    def get_all_st_storage_cost_variation_withdrawal(self) -> StStorageSeriesMapping:
        return self._get_all_sts_matrix(COST_VARIATION_WITHDRAWAL_TABLE)

    @override
    def get_st_storage_additional_constraint_matrix(
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
            self._raise_the_right_constraint_exception({area_id: {storage_id: constraint_id}})
        return self.get_impl().get_matrix(row.matrix_id, default_empty_supplier=default_scenario_hourly)

    @override
    def get_all_st_storage_additional_constraint_matrices(self) -> StStorageConstraintSeriesMapping:
        result: StStorageConstraintSeriesMapping = {}
        table = ST_STORAGE_ADDITIONAL_CONSTRAINT_MATRIX_TABLE
        stmt = select(table).where(table.c.study_id == self._study_id)
        rows = self._db_session.execute(stmt).fetchall()
        for row in rows:
            result.setdefault(row.area_id, {}).setdefault(row.st_storage_id, {})[row.constraint_id] = row.matrix_id
        return result

    @override
    def save_st_storage_constraint_matrices(self, series: StStorageConstraintSeriesMapping) -> None:
        study_id = self._study_id
        session = self._db_session

        values = []
        for area_id, value in series.items():
            for sts_id, v in value.items():
                for constraint_id, matrix_id in v.items():
                    data = {
                        "study_id": study_id,
                        "area_id": area_id,
                        "st_storage_id": sts_id,
                        "constraint_id": constraint_id,
                        "matrix_id": matrix_id,
                    }
                    values.append(data)

        try:
            upsert_multiple(session, ST_STORAGE_ADDITIONAL_CONSTRAINT_MATRIX_TABLE, values)
        except IntegrityError as e:
            invalid_data = {
                area_id: {sts_id: constraint_id for sts_id, constraints in v.items() for constraint_id in constraints}
                for area_id, v in series.items()
            }
            self._raise_the_right_constraint_exception(invalid_data, e)

        session.commit()

    def _get_st_storage_matrix_row(self, area_id: str, storage_id: str, table: Table) -> Row[Any] | None:
        stmt = select(table).where(
            (table.c.study_id == self._study_id) & (table.c.area_id == area_id) & (table.c.st_storage_id == storage_id)
        )
        return self._db_session.execute(stmt).fetchone()

    def _get_st_storage_matrix(self, area_id: str, storage_id: str, table: Table) -> SeriesId:
        row = self._get_st_storage_matrix_row(area_id, storage_id, table)
        if not row:
            self._raise_the_right_storage_exception({area_id: [storage_id]})
        return str(row.matrix_id)
