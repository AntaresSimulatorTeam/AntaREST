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

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict

import numpy as np
import polars as pl
from sqlalchemy import Row, delete, insert, select
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import (
    HydroAllocationNotFound,
    HydroConfigNotFound,
    HydroInflowStructureNotFound,
)
from antarest.study.business.model.config.compatibility_parameters_model import HydroPmax
from antarest.study.business.model.hydro_allocation_model import HydroAllocation, HydroAllocationArea
from antarest.study.business.model.hydro_correlation_model import (
    HydroCorrelation,
    HydroCorrelationMatrix,
)
from antarest.study.business.model.hydro_model import HydroManagement, HydroProperties, InflowStructure
from antarest.study.dao.api.hydro_dao import HydroDao
from antarest.study.dao.database.common import validate_area_exists, validate_areas_exists
from antarest.study.dao.database.models.area import AREA_TABLE
from antarest.study.dao.database.models.hydro import (
    HYDRO_ALLOCATION_TABLE,
    HYDRO_CORRELATION_TABLE,
    HYDRO_INFLOW_STRUCTURE_TABLE,
    HYDRO_MANAGEMENT_TABLE,
)
from antarest.study.dao.database.sql_utils import upsert_one

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
        return HydroManagement(
            inter_daily_breakdown=row.inter_daily_breakdown,
            intra_daily_modulation=row.intra_daily_modulation,
            inter_monthly_breakdown=row.inter_monthly_breakdown,
            reservoir=row.reservoir,
            reservoir_capacity=row.reservoir_capacity,
            follow_load=row.follow_load,
            use_water=row.use_water,
            hard_bounds=row.hard_bounds,
            initialize_reservoir_date=row.initialize_reservoir_date,
            use_heuristic=row.use_heuristic,
            power_to_level=row.power_to_level,
            use_leeway=row.use_leeway,
            leeway_low=row.leeway_low,
            leeway_up=row.leeway_up,
            pumping_efficiency=row.pumping_efficiency,
            overflow_spilled_cost_difference=row.overflow_spilled_cost_difference,
        )

    @staticmethod
    def _convert_row_to_inflow_structure(row: Row[Any]) -> InflowStructure:
        """Convert a database row to InflowStructure model."""
        return InflowStructure(inter_monthly_correlation=row.inter_monthly_correlation)

    @staticmethod
    def _hydro_management_to_dict(hydro_management: HydroManagement) -> dict[str, Any]:
        """Convert HydroManagement model to dict for database insert/update."""
        return {
            "inter_daily_breakdown": hydro_management.inter_daily_breakdown,
            "intra_daily_modulation": hydro_management.intra_daily_modulation,
            "inter_monthly_breakdown": hydro_management.inter_monthly_breakdown,
            "reservoir": hydro_management.reservoir,
            "reservoir_capacity": hydro_management.reservoir_capacity,
            "follow_load": hydro_management.follow_load,
            "use_water": hydro_management.use_water,
            "hard_bounds": hydro_management.hard_bounds,
            "initialize_reservoir_date": hydro_management.initialize_reservoir_date,
            "use_heuristic": hydro_management.use_heuristic,
            "power_to_level": hydro_management.power_to_level,
            "use_leeway": hydro_management.use_leeway,
            "leeway_low": hydro_management.leeway_low,
            "leeway_up": hydro_management.leeway_up,
            "pumping_efficiency": hydro_management.pumping_efficiency,
            "overflow_spilled_cost_difference": hydro_management.overflow_spilled_cost_difference,
        }

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
            HydroConfigNotFound: If hydro management config does not exist for the area.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        validate_area_exists(session, study_id, area_id)

        stmt = select(HYDRO_MANAGEMENT_TABLE).where(
            (HYDRO_MANAGEMENT_TABLE.c.study_id == study_id) & (HYDRO_MANAGEMENT_TABLE.c.area_id == area_id)
        )
        row = session.execute(stmt).fetchone()

        if not row:
            raise HydroConfigNotFound(area_id)

        return self._convert_row_to_hydro_management(row)

    @override
    def save_hydro_management(self, hydro_management: HydroManagement, area_id: str) -> None:
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

        validate_area_exists(session, study_id, area_id)

        values = self._hydro_management_to_dict(hydro_management)
        values["study_id"] = study_id
        values["area_id"] = area_id
        upsert_one(session, HYDRO_MANAGEMENT_TABLE, values)

        session.commit()

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
            HydroInflowStructureNotFound: If inflow structure does not exist for the area.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        validate_area_exists(session, study_id, area_id)

        stmt = select(HYDRO_INFLOW_STRUCTURE_TABLE).where(
            (HYDRO_INFLOW_STRUCTURE_TABLE.c.study_id == study_id) & (HYDRO_INFLOW_STRUCTURE_TABLE.c.area_id == area_id)
        )
        row = session.execute(stmt).fetchone()

        if not row:
            raise HydroInflowStructureNotFound(area_id)

        return self._convert_row_to_inflow_structure(row)

    @override
    def save_inflow_structure(self, inflow_structure: InflowStructure, area_id: str) -> None:
        """
        Save inflow structure configuration for an area.

        Args:
            inflow_structure: The InflowStructure configuration to save.
            area_id: The area identifier.

        Raises:
            AreaNotFound: If the area does not exist.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        validate_area_exists(session, study_id, area_id)

        values = {
            "study_id": study_id,
            "area_id": area_id,
            "inter_monthly_correlation": inflow_structure.inter_monthly_correlation,
        }
        upsert_one(session, HYDRO_INFLOW_STRUCTURE_TABLE, values)

        session.commit()

    @override
    def get_all_hydro_properties(self) -> Dict[str, HydroProperties]:
        """
        Get all hydro properties for all areas in the study.

        Returns:
            Dictionary mapping area_id to HydroProperties (management_options + inflow_structure).

        Raises:
            HydroConfigNotFound: If any area is missing hydro management configuration.
            HydroInflowStructureNotFound: If any area is missing inflow structure configuration.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Get ALL areas in the study
        stmt_areas = select(AREA_TABLE.c.area_id).where(AREA_TABLE.c.study_id == study_id)
        all_area_ids = [row.area_id for row in session.execute(stmt_areas)]

        # Get all hydro management records for all areas
        stmt_management = select(HYDRO_MANAGEMENT_TABLE).where(HYDRO_MANAGEMENT_TABLE.c.study_id == study_id)
        management_rows = session.execute(stmt_management).fetchall()

        # Get all inflow structure records for all areas
        stmt_inflow = select(HYDRO_INFLOW_STRUCTURE_TABLE).where(HYDRO_INFLOW_STRUCTURE_TABLE.c.study_id == study_id)
        inflow_rows = session.execute(stmt_inflow).fetchall()

        # Build lookup dictionaries
        management_by_area = {row.area_id: self._convert_row_to_hydro_management(row) for row in management_rows}
        inflow_by_area = {row.area_id: self._convert_row_to_inflow_structure(row) for row in inflow_rows}

        # Build result for ALL areas (hydro data is mandatory)
        result: Dict[str, HydroProperties] = {}
        for area_id in all_area_ids:
            if area_id not in management_by_area:
                raise HydroConfigNotFound(area_id)
            if area_id not in inflow_by_area:
                raise HydroInflowStructureNotFound(area_id)

            result[area_id] = HydroProperties(
                management_options=management_by_area[area_id],
                inflow_structure=inflow_by_area[area_id],
            )

        return result

    @override
    def get_hydro_allocation(self, area_id: str) -> HydroAllocation:
        """
        Get hydro allocation for a specific area.

        Args:
            area_id: The source area identifier.

        Returns:
            HydroAllocation containing the allocation coefficients.
            Returns empty allocation if no allocation data exists.

        Raises:
            AreaNotFound: If the area does not exist.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        validate_area_exists(session, study_id, area_id)

        stmt = select(HYDRO_ALLOCATION_TABLE).where(
            (HYDRO_ALLOCATION_TABLE.c.study_id == study_id) & (HYDRO_ALLOCATION_TABLE.c.source_area_id == area_id)
        )
        rows = session.execute(stmt).fetchall()

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
            HydroAllocationNotFound: If no hydro allocation data is found for the study.

        """
        study_id = self.get_study_id()
        session = self.get_session()

        stmt = select(HYDRO_ALLOCATION_TABLE).where(HYDRO_ALLOCATION_TABLE.c.study_id == study_id)
        rows = session.execute(stmt).fetchall()

        if not rows:
            raise HydroAllocationNotFound(study_id)

        # Group by source area
        allocations_by_source: dict[str, list[HydroAllocationArea]] = {}
        for row in rows:
            allocations_by_source.setdefault(row.source_area_id, []).append(
                HydroAllocationArea(area_id=row.target_area_id, coefficient=row.coefficient)
            )

        return {area_id: HydroAllocation(allocation=areas) for area_id, areas in allocations_by_source.items()}

    @override
    def save_hydro_allocation(self, area_id: str, allocation: HydroAllocation) -> None:
        """
        Save hydro allocation for a specific area.

        Args:
            area_id: The source area identifier.
            allocation: The HydroAllocation to save.

        Raises:
            AreaNotFound: If the source area or any target area does not exist.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Validate source area exists
        validate_area_exists(session, study_id, area_id)

        # Validate all target areas exist
        target_area_ids = {a.area_id for a in allocation.allocation}
        validate_areas_exists(session, study_id, target_area_ids)

        # Delete existing allocations for this source area
        stmt_delete = delete(HYDRO_ALLOCATION_TABLE).where(
            (HYDRO_ALLOCATION_TABLE.c.study_id == study_id) & (HYDRO_ALLOCATION_TABLE.c.source_area_id == area_id)
        )
        session.execute(stmt_delete)

        # Insert new allocations
        insert_values = [
            {
                "study_id": study_id,
                "source_area_id": area_id,
                "target_area_id": alloc_area.area_id,
                "coefficient": alloc_area.coefficient,
            }
            for alloc_area in allocation.allocation
        ]

        session.execute(insert(HYDRO_ALLOCATION_TABLE), insert_values)

        session.commit()

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
            AreaNotFound: If the area does not exist.
        """
        validate_area_exists(self.get_session(), self.get_study_id(), area_id)
        return self.get_hydro_correlation_matrix().to_hydro_correlations()[area_id]

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

        for row in rows:
            i = area_ids.index(row.area_from)
            j = area_ids.index(row.area_to)
            array[i][j] = row.coefficient
            array[j][i] = row.coefficient

        return HydroCorrelationMatrix(index=area_ids, columns=area_ids, data=array)

    @override
    def save_hydro_correlation(self, area_id: str, correlation: HydroCorrelation) -> None:
        """
        Save hydro correlation for a specific area.

        Args:
            area_id: The area identifier.
            correlation: The HydroCorrelation to save.

        Raises:
            AreaNotFound: If the area or any correlated area does not exist.
            ValueError: If the correlation matrix is invalid (via set_correlation validation).
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Validate area exists
        validate_area_exists(session, study_id, area_id)

        # Validate all correlated areas exist
        for corr_area in correlation.correlation:
            if corr_area.area_id != area_id:
                validate_area_exists(session, study_id, corr_area.area_id)

        # Get current matrix and apply changes (validates diagonal = 1, symmetry, etc.)
        current_correlation_matrix = self.get_hydro_correlation_matrix()
        current_correlation_matrix.set_correlation(area_id, correlation)

        # Get all area IDs for iterating the matrix
        area_ids = self.get_impl().get_all_area_ids()
        area_ids = sorted(area_ids)

        # Delete existing correlations
        # Delete all of them as the matrix is fully replaced
        stmt_delete = delete(HYDRO_CORRELATION_TABLE).where((HYDRO_CORRELATION_TABLE.c.study_id == study_id))
        session.execute(stmt_delete)

        # Insert new correlations (only upper triangle: area_from < area_to)
        # Diagonal is implicit, not stored
        insert_values = []
        for i in range(len(area_ids)):
            # not saved: values from the diagonal are always == 1.0
            for j in range(i + 1, len(area_ids)):
                coefficient = current_correlation_matrix.data[i][j]
                if not coefficient:
                    # null values are not saved
                    continue
                area_from = area_ids[i]
                area_to = area_ids[j]
                insert_values.append(
                    {
                        "study_id": study_id,
                        "area_from": area_from,
                        "area_to": area_to,
                        "coefficient": coefficient,
                    }
                )

        if insert_values:
            session.execute(insert(HYDRO_CORRELATION_TABLE), insert_values)

        session.commit()

    # ==================== Matrix Methods (NotImplementedError) ====================

    @override
    def get_hydro_maxpower(self, _area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_reservoir(self, _area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_energy(self, _area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_run_of_river(self, _area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_modulation(self, _area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_credit_modulations(self, _area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_inflow_pattern(self, _area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_water_values(self, _area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_mingen(self, _area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_max_hourly_gen_power(self, _area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_max_hourly_pump_power(self, _area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_max_daily_gen_energy(self, _area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_max_daily_pump_energy(self, _area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_maxpower(self, _area_id: str, _series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_reservoir(self, _area_id: str, _series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_energy(self, _area_id: str, _series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_run_of_river(self, _area_id: str, _series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_modulation(self, _area_id: str, _series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_credit_modulations(self, _area_id: str, _series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_inflow_pattern(self, _area_id: str, _series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_water_values(self, _area_id: str, _series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_mingen(self, _area_id: str, _series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_max_hourly_gen_power(self, _area_id: str, _series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_max_hourly_pump_power(self, _area_id: str, _series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_max_daily_gen_energy(self, _area_id: str, _series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_max_daily_pump_energy(self, _area_id: str, _series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def convert_hydro_pmax(self, _hydro_pmax: HydroPmax) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")
