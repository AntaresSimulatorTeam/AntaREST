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
Database implementation of HydroDao using SQLAlchemy Core.

This module provides database-backed storage for hydro configuration when storage_mode=DATABASE.
"""

import math
from abc import abstractmethod
from typing import TYPE_CHECKING, Any

import numpy as np
import polars as pl
from sqlalchemy import Row, Table, delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound
from antarest.core.utils.polars import create_polars_dataframe
from antarest.matrixstore.service import MATRIX_PROTOCOL_PREFIX
from antarest.study.business.model.config.compatibility_parameters_model import (
    HydroPmax,
)
from antarest.study.business.model.hydro_allocation_model import HydroAllocation, HydroAllocationArea
from antarest.study.business.model.hydro_correlation_model import (
    HydroCorrelation,
    HydroCorrelationMatrix,
)
from antarest.study.business.model.hydro_model import HydroManagement, HydroProperties, InflowStructure
from antarest.study.dao.api.hydro_dao import HydroDao
from antarest.study.dao.common import AreaId, AreaSeriesMapping
from antarest.study.dao.database.common import (
    get_all_area_matrices,
    get_row_representation_as_dict,
    save_area_matrix,
    validate_area_exists,
)
from antarest.study.dao.database.models.area import AREA_TABLE
from antarest.study.dao.database.models.hydro import (
    HYDRO_ALLOCATION_TABLE,
    HYDRO_CORRELATION_TABLE,
    HYDRO_CREDIT_MODULATIONS_TABLE,
    HYDRO_ENERGY_TABLE,
    HYDRO_INFLOW_PATTERN_TABLE,
    HYDRO_INFLOW_STRUCTURE_TABLE,
    HYDRO_MANAGEMENT_TABLE,
    HYDRO_MAX_DAILY_GEN_ENERGY_TABLE,
    HYDRO_MAX_DAILY_PUMP_ENERGY_TABLE,
    HYDRO_MAX_HOURLY_GEN_POWER_TABLE,
    HYDRO_MAX_HOURLY_PUMP_POWER_TABLE,
    HYDRO_MAXPOWER_TABLE,
    HYDRO_MINGEN_TABLE,
    HYDRO_MODULATION_TABLE,
    HYDRO_RESERVOIR_TABLE,
    HYDRO_RUN_OF_RIVER_TABLE,
    HYDRO_WATER_VALUES_TABLE,
)
from antarest.study.dao.database.sql_utils import upsert_multiple, upsert_one

_MANAGEMENT_COLS = [c for c in HYDRO_MANAGEMENT_TABLE.c if c.name not in ("study_id", "area_id")]

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


class DatabaseHydroDao(HydroDao):
    """Database implementation of HydroDao"""

    def __init__(self, study_id: str, db_session: Session) -> None:
        """
        Initialize DatabaseHydroDao with dependencies.

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

    @staticmethod
    def _convert_row_to_hydro_management(row: Row[Any]) -> HydroManagement:
        """Convert a database row to HydroManagement model."""
        data = get_row_representation_as_dict(row)
        return HydroManagement(**{c.name: data[c.name] for c in _MANAGEMENT_COLS})

    @staticmethod
    def _convert_row_to_inflow_structure(row: Row[Any]) -> InflowStructure:
        """Convert a database row to InflowStructure model."""
        return InflowStructure(inter_monthly_correlation=row.inter_monthly_correlation)

    @override
    def get_hydro_management(self, area_id: str) -> HydroManagement:
        """
        Get hydro management configuration for an area.

        Args:
            area_id: The area identifier.

        Returns:
            HydroManagement configuration for the area.

        Raises:
            AreaNotFound: If the area does not exist.
            ValueError: If the area exists but has no hydro management configuration.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        stmt = select(HYDRO_MANAGEMENT_TABLE).where(
            (HYDRO_MANAGEMENT_TABLE.c.study_id == study_id) & (HYDRO_MANAGEMENT_TABLE.c.area_id == area_id)
        )
        row = session.execute(stmt).fetchone()

        if not row:
            validate_area_exists(session, study_id, area_id)
            raise ValueError(f"Hydro management not found for area '{area_id}'")

        return self._convert_row_to_hydro_management(row)

    def _raise_the_right_area_exception(self, area_ids: set[AreaId], exc: IntegrityError | None = None) -> None:
        # Happens if some areas did not exist -> ForeignKey constraint fails

        if invalid_areas := self.get_impl().get_invalid_area_ids(list(area_ids)):
            raise AreaNotFound(*invalid_areas)

        # All areas exist. It means that the DB table does not contain the information.
        raise ValueError("One of the link table is not filled as it should") from exc

    @override
    def save_hydro_management(self, hydro_management: dict[AreaId, HydroManagement]) -> None:
        """
        Save hydro management configuration for an area.

        Args:
            hydro_management: The HydroManagement configuration to save.
            area_id: The area identifier.

        Raises:
            AreaNotFound: If the area does not exist.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        values = []
        for area_id, management in hydro_management.items():
            values.append({"study_id": study_id, "area_id": area_id, **management.model_dump()})

        try:
            upsert_multiple(session, HYDRO_MANAGEMENT_TABLE, values)
            session.commit()
        except IntegrityError as e:
            session.rollback()
            # IntegrityError occurred can only mean that an area_id is invalid
            self._raise_the_right_area_exception(set(hydro_management), e)

    @override
    def get_inflow_structure(self, area_id: str) -> InflowStructure:
        """
        Get inflow structure configuration for an area.

        Args:
            area_id: The area identifier.

        Returns:
            InflowStructure configuration for the area.

        Raises:
            AreaNotFound: If the area does not exist.
            ValueError: If the area exists but has no inflow structure configuration.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        stmt = select(HYDRO_INFLOW_STRUCTURE_TABLE).where(
            (HYDRO_INFLOW_STRUCTURE_TABLE.c.study_id == study_id) & (HYDRO_INFLOW_STRUCTURE_TABLE.c.area_id == area_id)
        )
        row = session.execute(stmt).fetchone()

        if not row:
            validate_area_exists(session, study_id, area_id)
            raise ValueError(f"Inflow structure not found for area '{area_id}'")

        return self._convert_row_to_inflow_structure(row)

    @override
    def save_inflow_structure(self, inflow_structure: dict[AreaId, InflowStructure]) -> None:
        """Save inflow structure configuration for several areas"""
        study_id = self.get_study_id()
        session = self.get_session()

        values = []
        for area_id, inflow in inflow_structure.items():
            values.append(
                {
                    "study_id": study_id,
                    "area_id": area_id,
                    "inter_monthly_correlation": inflow.inter_monthly_correlation,
                }
            )

        try:
            upsert_multiple(session, HYDRO_INFLOW_STRUCTURE_TABLE, values)
            session.commit()
        except IntegrityError as e:
            session.rollback()
            # IntegrityError occurred can only mean that an area_id is invalid
            self._raise_the_right_area_exception(set(inflow_structure), e)

    @override
    def get_all_hydro_properties(self) -> dict[str, HydroProperties]:
        """
        Get all hydro properties for all areas in the study.

        Returns:
            Dictionary mapping area_id to HydroProperties (management_options + inflow_structure).
        """
        study_id = self.get_study_id()
        session = self.get_session()

        stmt = (
            select(
                AREA_TABLE.c.area_id,
                *_MANAGEMENT_COLS,
                HYDRO_INFLOW_STRUCTURE_TABLE.c.inter_monthly_correlation,
            )
            .join(
                HYDRO_MANAGEMENT_TABLE,
                (AREA_TABLE.c.study_id == HYDRO_MANAGEMENT_TABLE.c.study_id)
                & (AREA_TABLE.c.area_id == HYDRO_MANAGEMENT_TABLE.c.area_id),
            )
            .join(
                HYDRO_INFLOW_STRUCTURE_TABLE,
                (AREA_TABLE.c.study_id == HYDRO_INFLOW_STRUCTURE_TABLE.c.study_id)
                & (AREA_TABLE.c.area_id == HYDRO_INFLOW_STRUCTURE_TABLE.c.area_id),
            )
            .where(AREA_TABLE.c.study_id == study_id)
        )
        rows = session.execute(stmt).fetchall()

        return {
            row.area_id: HydroProperties(
                management_options=self._convert_row_to_hydro_management(row),
                inflow_structure=self._convert_row_to_inflow_structure(row),
            )
            for row in rows
        }

    @override
    def get_hydro_allocation(self, area_id: str) -> HydroAllocation:
        """
        Get hydro allocation for a specific area.

        Args:
            area_id: The source area identifier.

        Returns:
            HydroAllocation containing the allocation coefficients.

        Raises:
            AreaNotFound: If the area does not exist.
            ValueError: If the area exists but has no allocation data.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        stmt = select(HYDRO_ALLOCATION_TABLE).where(
            (HYDRO_ALLOCATION_TABLE.c.study_id == study_id) & (HYDRO_ALLOCATION_TABLE.c.source_area_id == area_id)
        )
        rows = session.execute(stmt).fetchall()

        if not rows:
            validate_area_exists(session, study_id, area_id)
            raise ValueError(f"Hydro allocation not found for area '{area_id}'")

        allocation_areas = [
            HydroAllocationArea(area_id=row.target_area_id, coefficient=row.coefficient) for row in rows
        ]
        return HydroAllocation(allocation=allocation_areas)

    @override
    def get_hydro_allocation_matrix(self) -> dict[str, HydroAllocation]:
        """
        Get all hydro allocations for the study as a dictionary.

        Returns:
            Dictionary mapping source area_id to HydroAllocation.

        Raises:
            ValueError: If no hydro allocation data is found for the study.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        stmt = select(HYDRO_ALLOCATION_TABLE).where(HYDRO_ALLOCATION_TABLE.c.study_id == study_id)
        rows = session.execute(stmt).fetchall()

        if not rows:
            raise ValueError(f"Hydro allocation not found for study '{study_id}'")

        # Group by source area
        allocations_by_source: dict[str, list[HydroAllocationArea]] = {}
        for row in rows:
            allocations_by_source.setdefault(row.source_area_id, []).append(
                HydroAllocationArea(area_id=row.target_area_id, coefficient=row.coefficient)
            )

        return {area_id: HydroAllocation(allocation=areas) for area_id, areas in allocations_by_source.items()}

    @override
    def save_hydro_allocation(self, allocation_dict: dict[AreaId, HydroAllocation]) -> None:
        """
        Save hydro allocation for specific areas.

        This will replace any existing allocation for the given areas.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Delete existing allocations for the source areas
        stmt_delete = delete(HYDRO_ALLOCATION_TABLE).where(
            (HYDRO_ALLOCATION_TABLE.c.study_id == study_id)
            & (HYDRO_ALLOCATION_TABLE.c.source_area_id.in_(set(allocation_dict)))
        )
        session.execute(stmt_delete)

        # Insert new allocations
        insert_values = []
        for area_id, allocation in allocation_dict.items():
            for alloc_area in allocation.allocation:
                insert_values.append(
                    {
                        "study_id": study_id,
                        "source_area_id": area_id,
                        "target_area_id": alloc_area.area_id,
                        "coefficient": alloc_area.coefficient,
                    }
                )

        try:
            session.execute(insert(HYDRO_ALLOCATION_TABLE), insert_values)
            session.commit()
        except IntegrityError as e:
            # IntegrityError occurred can only mean that an area_id is invalid
            session.rollback()
            # Build the `all_area_ids` set to raise the proper exception
            all_area_ids = set()
            for area_id, allocation in allocation_dict.items():
                all_area_ids.add(area_id)
                for alloc in allocation.allocation:
                    all_area_ids.add(alloc.area_id)
            self._raise_the_right_area_exception(set(all_area_ids), e)

    @override
    def get_hydro_correlation(self, area_id: str) -> HydroCorrelation:
        """
        Get hydro correlation for a specific area.

        Args:
            area_id: The area identifier.

        Returns:
            HydroCorrelation containing the correlation coefficients for all areas.
            Self-correlation is always 100%, missing correlations default to 0%.

        Raises:
            ValueError: If the area does not exist.
        """
        correlations = self.get_hydro_correlation_matrix().to_hydro_correlations()
        if area_id not in correlations:
            raise ValueError(f"Area '{area_id}' not found in correlation matrix")
        return correlations[area_id]

    @override
    def get_hydro_correlation_matrix(self) -> HydroCorrelationMatrix:
        """
        Get the full hydro correlation matrix for the study.

        Returns:
            HydroCorrelationMatrix with all area correlations.
            Returns identity matrix (self=1.0, rest=0.0) if no correlations stored.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Get all area IDs from the study
        area_ids = self.get_impl().get_all_area_ids()
        area_ids = sorted(area_ids)

        # Start with identity matrix (diagonal = 1, rest = 0)
        array = np.identity(len(area_ids))

        # Get stored correlations and fill the matrix
        stmt = select(HYDRO_CORRELATION_TABLE).where(HYDRO_CORRELATION_TABLE.c.study_id == study_id)
        rows = session.execute(stmt).fetchall()

        area_index = {area_id: i for i, area_id in enumerate(area_ids)}
        for row in rows:
            i = area_index[row.area_from]
            j = area_index[row.area_to]
            array[i][j] = row.coefficient
            array[j][i] = row.coefficient

        return HydroCorrelationMatrix(index=area_ids, columns=area_ids, data=array)

    @override
    def save_hydro_correlation(self, area_id: str, correlation: HydroCorrelation) -> None:
        """
        Save hydro correlation for a specific area.

        This will replace any existing correlation for the area.

        Args:
            area_id: The area identifier.
            correlation: The HydroCorrelation to save.

        Raises:
            AreaNotFound: If the area or any correlated area does not exist.
            ValueError: If self-correlation is provided and is not 100%.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Validate self-correlation if provided
        for corr_area in correlation.correlation:
            if corr_area.area_id == area_id and not math.isclose(corr_area.coefficient, 100.0):
                raise ValueError(f"Self-correlation for area '{area_id}' must be 100%, got {corr_area.coefficient}%")

        # Delete existing correlations involving this area
        stmt_delete = delete(HYDRO_CORRELATION_TABLE).where(
            (HYDRO_CORRELATION_TABLE.c.study_id == study_id)
            & ((HYDRO_CORRELATION_TABLE.c.area_from == area_id) | (HYDRO_CORRELATION_TABLE.c.area_to == area_id))
        )
        session.execute(stmt_delete)

        # Insert new correlations in canonical upper-triangle order (area_from < area_to)
        insert_values = []
        for corr_area in correlation.correlation:
            if corr_area.area_id == area_id or corr_area.coefficient == 0:
                continue
            coefficient = corr_area.coefficient / 100
            a, b = sorted([area_id, corr_area.area_id])
            insert_values.append(
                {
                    "study_id": study_id,
                    "area_from": a,
                    "area_to": b,
                    "coefficient": coefficient,
                }
            )

        try:
            if insert_values:
                session.execute(insert(HYDRO_CORRELATION_TABLE), insert_values)
            session.commit()
        except IntegrityError as e:
            session.rollback()
            all_area_ids = [area_id] + [corr_area.area_id for corr_area in correlation.correlation]
            invalid = self.get_impl().get_invalid_area_ids(all_area_ids)
            raise AreaNotFound(*invalid) from e

    # ==================== Matrix Methods ====================

    def _get_hydro_matrix(self, area_id: str, table: Table) -> pl.DataFrame:
        study_id = self.get_study_id()
        session = self.get_session()
        stmt = select(table).where((table.c.study_id == study_id) & (table.c.area_id == area_id))
        row = session.execute(stmt).fetchone()
        if not row:
            validate_area_exists(session, study_id, area_id)
            raise ValueError(f"Hydro matrix not found for area '{area_id}' in table '{table.name}'")
        return self.get_impl().get_matrix(row.matrix_id)

    def _save_hydro_matrix(self, area_id: str, table: Table, matrix_id: str) -> None:
        session = self.get_session()
        study_id = self.get_study_id()
        values = {"study_id": study_id, "area_id": area_id, "matrix_id": matrix_id}
        try:
            upsert_one(session, table, values)
            session.commit()
        except IntegrityError as e:
            session.rollback()
            raise AreaNotFound(area_id) from e

    @override
    def get_hydro_maxpower(self, area_id: str) -> pl.DataFrame:
        return self._get_hydro_matrix(area_id, HYDRO_MAXPOWER_TABLE)

    @override
    def get_hydro_reservoir(self, area_id: str) -> pl.DataFrame:
        return self._get_hydro_matrix(area_id, HYDRO_RESERVOIR_TABLE)

    @override
    def get_hydro_energy(self, area_id: str) -> pl.DataFrame:
        return self._get_hydro_matrix(area_id, HYDRO_ENERGY_TABLE)

    @override
    def get_hydro_run_of_river(self, area_id: str) -> pl.DataFrame:
        return self._get_hydro_matrix(area_id, HYDRO_RUN_OF_RIVER_TABLE)

    @override
    def get_hydro_modulation(self, area_id: str) -> pl.DataFrame:
        return self._get_hydro_matrix(area_id, HYDRO_MODULATION_TABLE)

    @override
    def get_hydro_credit_modulations(self, area_id: str) -> pl.DataFrame:
        return self._get_hydro_matrix(area_id, HYDRO_CREDIT_MODULATIONS_TABLE)

    @override
    def get_hydro_inflow_pattern(self, area_id: str) -> pl.DataFrame:
        return self._get_hydro_matrix(area_id, HYDRO_INFLOW_PATTERN_TABLE)

    @override
    def get_hydro_water_values(self, area_id: str) -> pl.DataFrame:
        return self._get_hydro_matrix(area_id, HYDRO_WATER_VALUES_TABLE)

    @override
    def get_hydro_mingen(self, area_id: str) -> pl.DataFrame:
        return self._get_hydro_matrix(area_id, HYDRO_MINGEN_TABLE)

    @override
    def get_hydro_max_hourly_gen_power(self, area_id: str) -> pl.DataFrame:
        return self._get_hydro_matrix(area_id, HYDRO_MAX_HOURLY_GEN_POWER_TABLE)

    @override
    def get_hydro_max_hourly_pump_power(self, area_id: str) -> pl.DataFrame:
        return self._get_hydro_matrix(area_id, HYDRO_MAX_HOURLY_PUMP_POWER_TABLE)

    @override
    def get_hydro_max_daily_gen_energy(self, area_id: str) -> pl.DataFrame:
        return self._get_hydro_matrix(area_id, HYDRO_MAX_DAILY_GEN_ENERGY_TABLE)

    @override
    def get_hydro_max_daily_pump_energy(self, area_id: str) -> pl.DataFrame:
        return self._get_hydro_matrix(area_id, HYDRO_MAX_DAILY_PUMP_ENERGY_TABLE)

    @override
    def get_all_hydro_maxpower(self) -> AreaSeriesMapping:
        return get_all_area_matrices(self._study_id, self._db_session, HYDRO_MAXPOWER_TABLE)

    @override
    def get_all_hydro_reservoir(self) -> AreaSeriesMapping:
        return get_all_area_matrices(self._study_id, self._db_session, HYDRO_RESERVOIR_TABLE)

    @override
    def get_all_hydro_energy(self) -> AreaSeriesMapping:
        return get_all_area_matrices(self._study_id, self._db_session, HYDRO_ENERGY_TABLE)

    @override
    def get_all_hydro_run_of_river(self) -> AreaSeriesMapping:
        return get_all_area_matrices(self._study_id, self._db_session, HYDRO_RUN_OF_RIVER_TABLE)

    @override
    def get_all_hydro_modulation(self) -> AreaSeriesMapping:
        return get_all_area_matrices(self._study_id, self._db_session, HYDRO_MODULATION_TABLE)

    @override
    def get_all_hydro_credit_modulations(self) -> AreaSeriesMapping:
        return get_all_area_matrices(self._study_id, self._db_session, HYDRO_CREDIT_MODULATIONS_TABLE)

    @override
    def get_all_hydro_inflow_pattern(self) -> AreaSeriesMapping:
        return get_all_area_matrices(self._study_id, self._db_session, HYDRO_INFLOW_PATTERN_TABLE)

    @override
    def get_all_hydro_water_values(self) -> AreaSeriesMapping:
        return get_all_area_matrices(self._study_id, self._db_session, HYDRO_WATER_VALUES_TABLE)

    @override
    def get_all_hydro_mingen(self) -> AreaSeriesMapping:
        return get_all_area_matrices(self._study_id, self._db_session, HYDRO_MINGEN_TABLE)

    @override
    def get_all_hydro_max_hourly_gen_power(self) -> AreaSeriesMapping:
        return get_all_area_matrices(self._study_id, self._db_session, HYDRO_MAX_HOURLY_GEN_POWER_TABLE)

    @override
    def get_all_hydro_max_hourly_pump_power(self) -> AreaSeriesMapping:
        return get_all_area_matrices(self._study_id, self._db_session, HYDRO_MAX_HOURLY_PUMP_POWER_TABLE)

    @override
    def get_all_hydro_max_daily_gen_energy(self) -> AreaSeriesMapping:
        return get_all_area_matrices(self._study_id, self._db_session, HYDRO_MAX_DAILY_GEN_ENERGY_TABLE)

    @override
    def get_all_hydro_max_daily_pump_energy(self) -> AreaSeriesMapping:
        return get_all_area_matrices(self._study_id, self._db_session, HYDRO_MAX_DAILY_PUMP_ENERGY_TABLE)

    @override
    def save_hydro_maxpower(self, series: AreaSeriesMapping) -> None:
        save_area_matrix(self.get_impl(), series, HYDRO_MAXPOWER_TABLE)

    @override
    def save_hydro_reservoir(self, series: AreaSeriesMapping) -> None:
        save_area_matrix(self.get_impl(), series, HYDRO_RESERVOIR_TABLE)

    @override
    def save_hydro_energy(self, series: AreaSeriesMapping) -> None:
        save_area_matrix(self.get_impl(), series, HYDRO_ENERGY_TABLE)

    @override
    def save_hydro_run_of_river(self, series: AreaSeriesMapping) -> None:
        save_area_matrix(self.get_impl(), series, HYDRO_RUN_OF_RIVER_TABLE)

    @override
    def save_hydro_modulation(self, series: AreaSeriesMapping) -> None:
        save_area_matrix(self.get_impl(), series, HYDRO_MODULATION_TABLE)

    @override
    def save_hydro_credit_modulations(self, series: AreaSeriesMapping) -> None:
        save_area_matrix(self.get_impl(), series, HYDRO_CREDIT_MODULATIONS_TABLE)

    @override
    def save_hydro_inflow_pattern(self, series: AreaSeriesMapping) -> None:
        save_area_matrix(self.get_impl(), series, HYDRO_INFLOW_PATTERN_TABLE)

    @override
    def save_hydro_water_values(self, series: AreaSeriesMapping) -> None:
        save_area_matrix(self.get_impl(), series, HYDRO_WATER_VALUES_TABLE)

    @override
    def save_hydro_mingen(self, series: AreaSeriesMapping) -> None:
        save_area_matrix(self.get_impl(), series, HYDRO_MINGEN_TABLE)

    @override
    def save_hydro_max_hourly_gen_power(self, series: AreaSeriesMapping) -> None:
        save_area_matrix(self.get_impl(), series, HYDRO_MAX_HOURLY_GEN_POWER_TABLE)

    @override
    def save_hydro_max_hourly_pump_power(self, series: AreaSeriesMapping) -> None:
        save_area_matrix(self.get_impl(), series, HYDRO_MAX_HOURLY_PUMP_POWER_TABLE)

    @override
    def save_hydro_max_daily_gen_energy(self, series: AreaSeriesMapping) -> None:
        save_area_matrix(self.get_impl(), series, HYDRO_MAX_DAILY_GEN_ENERGY_TABLE)

    @override
    def save_hydro_max_daily_pump_energy(self, series: AreaSeriesMapping) -> None:
        save_area_matrix(self.get_impl(), series, HYDRO_MAX_DAILY_PUMP_ENERGY_TABLE)

    @override
    def convert_hydro_pmax(self, hydro_pmax: HydroPmax) -> None:
        compatibility_data = self.get_impl().get_compatibility_parameters()
        if compatibility_data.hydro_pmax == hydro_pmax:
            return

        study_id = self.get_study_id()
        session = self.get_session()

        if hydro_pmax == HydroPmax.HOURLY:
            area_ids = self.get_impl().get_all_area_ids()
            generator = self.get_impl()._generator_matrix_constants
            hourly_matrix_id = generator.get_null_matrix().removeprefix(MATRIX_PROTOCOL_PREFIX)
            daily_matrix_id = generator.matrix_service.create(create_polars_dataframe(np.full((365, 1), 24)))

            hourly_rows = [
                {"study_id": study_id, "area_id": area_id, "matrix_id": hourly_matrix_id} for area_id in area_ids
            ]
            daily_rows = [
                {"study_id": study_id, "area_id": area_id, "matrix_id": daily_matrix_id} for area_id in area_ids
            ]
            try:
                upsert_multiple(session, HYDRO_MAX_HOURLY_GEN_POWER_TABLE, hourly_rows)
                upsert_multiple(session, HYDRO_MAX_HOURLY_PUMP_POWER_TABLE, hourly_rows)
                upsert_multiple(session, HYDRO_MAX_DAILY_GEN_ENERGY_TABLE, daily_rows)
                upsert_multiple(session, HYDRO_MAX_DAILY_PUMP_ENERGY_TABLE, daily_rows)
                session.commit()
            except IntegrityError as e:
                session.rollback()
                invalid = self.get_impl().get_invalid_area_ids(area_ids)
                raise AreaNotFound(*invalid) from e
        else:
            for table in [
                HYDRO_MAX_HOURLY_GEN_POWER_TABLE,
                HYDRO_MAX_HOURLY_PUMP_POWER_TABLE,
                HYDRO_MAX_DAILY_GEN_ENERGY_TABLE,
                HYDRO_MAX_DAILY_PUMP_ENERGY_TABLE,
            ]:
                session.execute(delete(table).where(table.c.study_id == study_id))
            session.commit()

        compatibility_data.hydro_pmax = hydro_pmax
        self.get_impl().save_compatibility_parameters(compatibility_data)
