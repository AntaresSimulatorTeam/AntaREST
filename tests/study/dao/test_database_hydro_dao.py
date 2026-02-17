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

import numpy as np
import polars as pl
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.core.exceptions import AreaNotFound
from antarest.study.business.model.hydro_allocation_model import HydroAllocation, HydroAllocationArea
from antarest.study.business.model.hydro_correlation_model import (
    HydroCorrelation,
    HydroCorrelationArea,
)
from antarest.study.business.model.hydro_model import HydroManagement, InflowStructure
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
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


class TestHydroManagement:
    """Tests for hydro management CRUD operations."""

    def test_get_hydro_management_raises_error_for_area_without_hydro_config(self, dao: DatabaseStudyDao) -> None:
        """Test that get_hydro_management raises ValueError for an area without hydro config."""
        dao.save_area("Paris")

        with pytest.raises(ValueError):
            dao.get_hydro_management("paris")

    def test_get_hydro_management_raises_error_for_nonexistent_area(self, dao: DatabaseStudyDao) -> None:
        """Test that get_hydro_management raises AreaNotFound if area doesn't exist."""
        with pytest.raises(AreaNotFound):
            dao.get_hydro_management("nonexistent")

    def test_save_hydro_management_updates_existing_record(self, dao: DatabaseStudyDao) -> None:
        """Test that save_hydro_management updates an existing record."""
        dao.save_area("Paris")

        # Create initial config
        hydro_mgmt1 = HydroManagement(reservoir=False, reservoir_capacity=100.0)
        dao.save_hydro_management(hydro_mgmt1, "paris")

        result = dao.get_hydro_management("paris")
        assert result.reservoir is False
        assert result.reservoir_capacity == 100.0

        # Update config
        hydro_mgmt2 = HydroManagement(reservoir=True, reservoir_capacity=999.0)
        dao.save_hydro_management(hydro_mgmt2, "paris")

        # Verify update
        result = dao.get_hydro_management("paris")
        assert result.reservoir is True
        assert result.reservoir_capacity == 999.0

    def test_save_hydro_management_raises_error_for_nonexistent_area(self, dao: DatabaseStudyDao) -> None:
        """Test that save_hydro_management raises AreaNotFound with the invalid area ID."""
        hydro_mgmt = HydroManagement()
        with pytest.raises(AreaNotFound, match="nonexistent"):
            dao.save_hydro_management(hydro_mgmt, "nonexistent")

    def test_hydro_management_with_version_specific_field(self, dao: DatabaseStudyDao) -> None:
        """Test that overflow_spilled_cost_difference (v9.2+) is handled correctly."""
        dao.save_area("Paris")

        # Defaults to None when not provided
        dao.save_hydro_management(HydroManagement(), "paris")
        assert dao.get_hydro_management("paris").overflow_spilled_cost_difference is None

        # Can be set to a value
        dao.save_hydro_management(HydroManagement(overflow_spilled_cost_difference=5.5), "paris")
        assert dao.get_hydro_management("paris").overflow_spilled_cost_difference == 5.5

        # Can be set back to None
        dao.save_hydro_management(HydroManagement(overflow_spilled_cost_difference=None), "paris")
        assert dao.get_hydro_management("paris").overflow_spilled_cost_difference is None


class TestInflowStructure:
    """Tests for inflow structure CRUD operations."""

    def test_get_inflow_structure_raises_error_for_area_without_config(self, dao: DatabaseStudyDao) -> None:
        """Test that get_inflow_structure raises ValueError for an area without config."""
        dao.save_area("Paris")

        with pytest.raises(ValueError):
            dao.get_inflow_structure("paris")

    def test_get_inflow_structure_raises_error_for_nonexistent_area(self, dao: DatabaseStudyDao) -> None:
        """Test that get_inflow_structure raises AreaNotFound if area doesn't exist."""
        with pytest.raises(AreaNotFound):
            dao.get_inflow_structure("nonexistent")

    def test_save_inflow_structure_updates_existing_record(self, dao: DatabaseStudyDao) -> None:
        """Test that save_inflow_structure updates an existing record."""
        dao.save_area("Paris")

        # Create initial config
        dao.save_inflow_structure(InflowStructure(inter_monthly_correlation=0.3), "paris")

        # Verify create
        result = dao.get_inflow_structure("paris")
        assert result.inter_monthly_correlation == 0.3

        # Update config
        dao.save_inflow_structure(InflowStructure(inter_monthly_correlation=0.9), "paris")

        # Verify update
        result = dao.get_inflow_structure("paris")
        assert result.inter_monthly_correlation == 0.9

    def test_save_inflow_structure_raises_error_for_nonexistent_area(self, dao: DatabaseStudyDao) -> None:
        """Test that save_inflow_structure raises AreaNotFound with the invalid area ID."""
        inflow = InflowStructure()
        with pytest.raises(AreaNotFound, match="nonexistent"):
            dao.save_inflow_structure(inflow, "nonexistent")


class TestGetAllHydroProperties:
    """Tests for get_all_hydro_properties aggregation."""

    def test_get_all_hydro_properties_returns_empty_dict_for_no_areas(self, dao: DatabaseStudyDao) -> None:
        """Test that get_all_hydro_properties returns empty dict when no areas exist."""
        result = dao.get_all_hydro_properties()
        assert result == {}

    def test_get_all_hydro_properties_excludes_areas_with_incomplete_data(self, dao: DatabaseStudyDao) -> None:
        """Test that areas missing management or inflow structure are excluded from results."""
        dao.save_area("Paris")
        dao.save_area("London")

        # Paris has only inflow, London has only management — neither is complete
        dao.save_inflow_structure(InflowStructure(inter_monthly_correlation=0.5), "paris")
        dao.save_hydro_management(HydroManagement(reservoir=True), "london")

        result = dao.get_all_hydro_properties()
        assert result == {}

    def test_get_all_hydro_properties_aggregates_data(self, dao: DatabaseStudyDao) -> None:
        """Test that get_all_hydro_properties correctly aggregates hydro data for all areas."""
        dao.save_area("Paris")
        dao.save_area("London")

        # Save complete hydro data for Paris
        dao.save_hydro_management(HydroManagement(reservoir=True, reservoir_capacity=500.0), "paris")
        dao.save_inflow_structure(InflowStructure(inter_monthly_correlation=0.6), "paris")

        # Save complete hydro data for London
        dao.save_hydro_management(HydroManagement(reservoir=False), "london")
        dao.save_inflow_structure(InflowStructure(inter_monthly_correlation=0.7), "london")

        result = dao.get_all_hydro_properties()

        assert len(result) == 2
        assert "paris" in result
        assert "london" in result

        # Check Paris data
        assert result["paris"].management_options.reservoir is True
        assert result["paris"].management_options.reservoir_capacity == 500.0
        assert result["paris"].inflow_structure.inter_monthly_correlation == 0.6

        # Check London data
        assert result["london"].management_options.reservoir is False
        assert result["london"].inflow_structure.inter_monthly_correlation == 0.7


class TestHydroAllocation:
    """Tests for hydro allocation CRUD operations."""

    def test_get_hydro_allocation_raises_error_for_area_without_allocation(self, dao: DatabaseStudyDao) -> None:
        """Test that get_hydro_allocation raises ValueError for an area without allocation."""
        dao.save_area("Paris")

        with pytest.raises(ValueError):
            dao.get_hydro_allocation("paris")

    def test_get_hydro_allocation_raises_error_for_nonexistent_area(self, dao: DatabaseStudyDao) -> None:
        """Test that get_hydro_allocation raises AreaNotFound if area doesn't exist."""
        with pytest.raises(AreaNotFound):
            dao.get_hydro_allocation("nonexistent")

    def test_save_hydro_allocation_replaces_existing_records(self, dao: DatabaseStudyDao) -> None:
        """Test that save_hydro_allocation replaces existing allocation."""
        dao.save_area("Paris")
        dao.save_area("London")

        # Create initial allocation
        dao.save_hydro_allocation(
            "paris", HydroAllocation(allocation=[HydroAllocationArea(area_id="paris", coefficient=1.0)])
        )

        # Replace with new allocation
        dao.save_hydro_allocation(
            "paris",
            HydroAllocation(
                allocation=[
                    HydroAllocationArea(area_id="paris", coefficient=0.6),
                    HydroAllocationArea(area_id="london", coefficient=0.4),
                ]
            ),
        )

        result = dao.get_hydro_allocation("paris")
        assert len(result.allocation) == 2

        # Check content regardless of ordering
        coeffs_by_area = {a.area_id: a.coefficient for a in result.allocation}
        assert coeffs_by_area == {"paris": 0.6, "london": 0.4}

    def test_save_hydro_allocation_raises_error_for_nonexistent_source_area(self, dao: DatabaseStudyDao) -> None:
        """Test that save_hydro_allocation raises AreaNotFound when source area doesn't exist."""
        dao.save_area("Paris")

        allocation = HydroAllocation(allocation=[HydroAllocationArea(area_id="paris", coefficient=1.0)])
        with pytest.raises(AreaNotFound, match="nonexistent"):
            dao.save_hydro_allocation("nonexistent", allocation)

    def test_save_hydro_allocation_raises_error_for_nonexistent_target_area(self, dao: DatabaseStudyDao) -> None:
        """Test that save_hydro_allocation raises AreaNotFound with the invalid target area ID."""
        dao.save_area("Paris")

        allocation = HydroAllocation(allocation=[HydroAllocationArea(area_id="nonexistent", coefficient=1.0)])
        with pytest.raises(AreaNotFound, match="nonexistent"):
            dao.save_hydro_allocation("paris", allocation)

    def test_get_hydro_allocation_matrix(self, dao: DatabaseStudyDao) -> None:
        """Test that get_hydro_allocation_matrix returns all allocations."""
        dao.save_area("Paris")
        dao.save_area("London")

        dao.save_hydro_allocation(
            "paris",
            HydroAllocation(
                allocation=[
                    HydroAllocationArea(area_id="paris", coefficient=0.7),
                    HydroAllocationArea(area_id="london", coefficient=0.3),
                ]
            ),
        )
        dao.save_hydro_allocation(
            "london", HydroAllocation(allocation=[HydroAllocationArea(area_id="london", coefficient=1.0)])
        )

        result = dao.get_hydro_allocation_matrix()

        assert len(result) == 2
        assert "paris" in result
        assert "london" in result
        assert len(result["paris"].allocation) == 2
        assert len(result["london"].allocation) == 1
        assert result["london"].allocation[0].coefficient == 1.0

        dao.save_hydro_allocation(
            "paris",
            HydroAllocation(
                allocation=[
                    HydroAllocationArea(area_id="paris", coefficient=0.2),
                ]
            ),
        )
        result = dao.get_hydro_allocation_matrix()
        assert len(result["paris"].allocation) == 1
        assert result["paris"].allocation[0].coefficient == 0.2
        assert result["london"].allocation[0].coefficient == 1.0


class TestHydroCorrelation:
    """Tests for hydro correlation CRUD operations."""

    def test_get_hydro_correlation_returns_self_correlation(self, dao: DatabaseStudyDao) -> None:
        """Test that get_hydro_correlation returns self-correlation for new area."""
        dao.save_area("Paris")

        correlation = dao.get_hydro_correlation("paris")

        assert len(correlation.correlation) == 1
        assert correlation.correlation[0].area_id == "paris"
        assert correlation.correlation[0].coefficient == 100.0  # Diagonal = 100%

        dao.save_area("Algiers")
        correlation = dao.get_hydro_correlation("paris")

        assert len(correlation.correlation) == 2
        assert correlation.correlation[0].area_id == "algiers"
        assert correlation.correlation[0].coefficient == 0.0  # Default correlation to other areas is zero
        assert correlation.correlation[1].area_id == "paris"
        assert correlation.correlation[1].coefficient == 100.0  # Diagonal = 100%

    def test_get_hydro_correlation_raises_error_for_nonexistent_area(self, dao: DatabaseStudyDao) -> None:
        """Test that get_hydro_correlation raises ValueError if area doesn't exist."""
        with pytest.raises(ValueError):
            dao.get_hydro_correlation("nonexistent")

    def test_save_hydro_correlation(self, dao: DatabaseStudyDao) -> None:
        """Test that correlation is stored symmetrically (only upper triangle)."""
        dao.save_area("Paris")
        dao.save_area("London")

        # Save from Paris perspective
        dao.save_hydro_correlation(
            "paris",
            HydroCorrelation(
                correlation=[
                    HydroCorrelationArea(area_id="paris", coefficient=100.0),
                    HydroCorrelationArea(area_id="london", coefficient=75.0),
                ]
            ),
        )

        # Get from London perspective should show same correlation
        london_corr = dao.get_hydro_correlation("london")

        # Find paris correlation in london's correlations
        paris_corr = next((c for c in london_corr.correlation if c.area_id == "paris"), None)
        assert paris_corr is not None
        assert paris_corr.coefficient == 75.0

    def test_save_hydro_correlation_raises_error_for_nonexistent_area(self, dao: DatabaseStudyDao) -> None:
        """Test that save_hydro_correlation raises AreaNotFound with the invalid area ID."""
        dao.save_area("Paris")

        # Nonexistent correlated area
        correlation = HydroCorrelation(
            correlation=[
                HydroCorrelationArea(area_id="nonexistent", coefficient=50.0),
            ]
        )
        with pytest.raises(AreaNotFound, match="nonexistent"):
            dao.save_hydro_correlation("paris", correlation)

        # Nonexistent source area
        correlation = HydroCorrelation(
            correlation=[
                HydroCorrelationArea(area_id="paris", coefficient=60.0),
            ]
        )
        with pytest.raises(AreaNotFound, match="nonexistent"):
            dao.save_hydro_correlation("nonexistent", correlation)

    def test_get_hydro_correlation_matrix(self, dao: DatabaseStudyDao) -> None:
        """Test that get_hydro_correlation_matrix returns the full matrix."""
        dao.save_area("Paris")
        dao.save_area("London")

        # Save correlation
        dao.save_hydro_correlation(
            "paris",
            HydroCorrelation(
                correlation=[
                    HydroCorrelationArea(area_id="paris", coefficient=100.0),
                    HydroCorrelationArea(area_id="london", coefficient=60.0),
                ]
            ),
        )
        result = dao.get_hydro_correlation_matrix()

        expected_matrix = [
            [1.0, 0.6],
            [0.6, 1.0],
        ]
        np.testing.assert_allclose(result.data, expected_matrix)

        # New area preserves matrix properties
        dao.save_area("Algiers")
        result = dao.get_hydro_correlation_matrix()
        expected_matrix = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.6],
            [0.0, 0.6, 1.0],
        ]
        np.testing.assert_allclose(result.data, expected_matrix)


class TestCascadeDelete:
    """Tests for cascade delete when area is deleted."""

    def test_cascade_delete_hydro_management(self, db_session: Session, dao: DatabaseStudyDao) -> None:
        """Test that hydro management is deleted when area is deleted."""
        dao.save_area("Paris")
        dao.save_hydro_management(HydroManagement(reservoir=True), "paris")

        # Delete area
        dao.delete_area("paris")

        # Verify hydro management is also deleted
        with db_session:
            stmt = select(HYDRO_MANAGEMENT_TABLE).where(
                (HYDRO_MANAGEMENT_TABLE.c.study_id == dao.get_study_id())
                & (HYDRO_MANAGEMENT_TABLE.c.area_id == "paris")
            )
            row = db_session.execute(stmt).fetchone()
            assert row is None

    def test_cascade_delete_inflow_structure(self, db_session: Session, dao: DatabaseStudyDao) -> None:
        """Test that inflow structure is deleted when area is deleted."""
        dao.save_area("Paris")
        dao.save_inflow_structure(InflowStructure(inter_monthly_correlation=0.8), "paris")

        # Delete area
        dao.delete_area("paris")

        # Verify inflow structure is also deleted
        with db_session:
            stmt = select(HYDRO_INFLOW_STRUCTURE_TABLE).where(
                (HYDRO_INFLOW_STRUCTURE_TABLE.c.study_id == dao.get_study_id())
                & (HYDRO_INFLOW_STRUCTURE_TABLE.c.area_id == "paris")
            )
            row = db_session.execute(stmt).fetchone()
            assert row is None

    def test_cascade_delete_hydro_allocation(self, db_session: Session, dao: DatabaseStudyDao) -> None:
        """Test that hydro allocation is deleted when source or target area is deleted."""
        dao.save_area("Paris")
        dao.save_area("London")
        dao.save_hydro_allocation(
            "paris",
            HydroAllocation(
                allocation=[
                    HydroAllocationArea(area_id="paris", coefficient=0.6),
                    HydroAllocationArea(area_id="london", coefficient=0.4),
                ]
            ),
        )

        # Delete target area allocation row referencing it should be cascade-deleted
        dao.delete_area("london")

        with db_session:
            stmt = select(HYDRO_ALLOCATION_TABLE).where(
                (HYDRO_ALLOCATION_TABLE.c.study_id == dao.get_study_id())
                & (HYDRO_ALLOCATION_TABLE.c.target_area_id == "london")
            )
            rows = db_session.execute(stmt).fetchall()
            assert len(rows) == 0

            stmt = select(HYDRO_ALLOCATION_TABLE).where(
                (HYDRO_ALLOCATION_TABLE.c.study_id == dao.get_study_id())
                & (HYDRO_ALLOCATION_TABLE.c.source_area_id == "paris")
            )
            rows = db_session.execute(stmt).fetchall()
            assert len(rows) == 1

        dao.save_area("London")
        dao.save_hydro_allocation(
            "paris",
            HydroAllocation(
                allocation=[
                    HydroAllocationArea(area_id="paris", coefficient=0.6),
                    HydroAllocationArea(area_id="london", coefficient=0.4),
                ]
            ),
        )

        # Delete source area remaining allocation rows should be cascade-deleted
        dao.delete_area("paris")

        with db_session:
            stmt = select(HYDRO_ALLOCATION_TABLE).where(
                (HYDRO_ALLOCATION_TABLE.c.study_id == dao.get_study_id())
                & (HYDRO_ALLOCATION_TABLE.c.source_area_id == "paris")
            )
            rows = db_session.execute(stmt).fetchall()
            assert len(rows) == 0

    def test_cascade_delete_hydro_correlation(self, db_session: Session, dao: DatabaseStudyDao) -> None:
        """Test that hydro correlation is deleted when area_from or area_to is deleted."""
        dao.save_area("Paris")
        dao.save_area("London")
        dao.save_area("Algiers")
        dao.save_hydro_correlation(
            "paris",
            HydroCorrelation(
                correlation=[
                    HydroCorrelationArea(area_id="london", coefficient=50.0),
                    HydroCorrelationArea(area_id="algiers", coefficient=60.0),
                ]
            ),
        )

        # Upper triangle stores: (algiers, paris, 0.6) and (london, paris, 0.5)
        with db_session:
            stmt = select(HYDRO_CORRELATION_TABLE).where(HYDRO_CORRELATION_TABLE.c.area_to == "paris")
            rows = db_session.execute(stmt).fetchall()
            assert len(rows) == 2

        # Delete london — row (london, paris) should be cascade-deleted via area_from FK
        dao.delete_area("london")

        with db_session:
            stmt = select(HYDRO_CORRELATION_TABLE).where(HYDRO_CORRELATION_TABLE.c.area_from == "london")
            rows = db_session.execute(stmt).fetchall()
            assert len(rows) == 0
            # (algiers, paris) row remains
            stmt = select(HYDRO_CORRELATION_TABLE).where(HYDRO_CORRELATION_TABLE.c.area_to == "paris")
            rows = db_session.execute(stmt).fetchall()
            assert len(rows) == 1

        # Delete paris — row (algiers, paris) should be cascade-deleted via area_to FK
        dao.delete_area("paris")

        with db_session:
            stmt = select(HYDRO_CORRELATION_TABLE).where(HYDRO_CORRELATION_TABLE.c.area_to == "paris")
            rows = db_session.execute(stmt).fetchall()
            assert len(rows) == 0


_ALL_HYDRO_MATRIX_TABLES = [
    HYDRO_MAXPOWER_TABLE,
    HYDRO_RESERVOIR_TABLE,
    HYDRO_ENERGY_TABLE,
    HYDRO_RUN_OF_RIVER_TABLE,
    HYDRO_MODULATION_TABLE,
    HYDRO_CREDIT_MODULATIONS_TABLE,
    HYDRO_INFLOW_PATTERN_TABLE,
    HYDRO_WATER_VALUES_TABLE,
    HYDRO_MINGEN_TABLE,
    HYDRO_MAX_HOURLY_GEN_POWER_TABLE,
    HYDRO_MAX_HOURLY_PUMP_POWER_TABLE,
    HYDRO_MAX_DAILY_GEN_ENERGY_TABLE,
    HYDRO_MAX_DAILY_PUMP_ENERGY_TABLE,
]


class TestHydroMatrices:
    """Tests for hydro matrix CRUD operations."""

    def test_save_and_get_all_hydro_matrices(self, dao: DatabaseStudyDao) -> None:
        """Test saving and retrieving all 13 hydro matrix types."""
        dao.save_area("Paris")

        matrix_service = dao._matrix_service
        dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
        series_id = matrix_service.create(dataframe)

        # Save all matrices
        dao.save_hydro_maxpower("paris", series_id)
        dao.save_hydro_reservoir("paris", series_id)
        dao.save_hydro_energy("paris", series_id)
        dao.save_hydro_run_of_river("paris", series_id)
        dao.save_hydro_modulation("paris", series_id)
        dao.save_hydro_credit_modulations("paris", series_id)
        dao.save_hydro_inflow_pattern("paris", series_id)
        dao.save_hydro_water_values("paris", series_id)
        dao.save_hydro_mingen("paris", series_id)
        dao.save_hydro_max_hourly_gen_power("paris", series_id)
        dao.save_hydro_max_hourly_pump_power("paris", series_id)
        dao.save_hydro_max_daily_gen_energy("paris", series_id)
        dao.save_hydro_max_daily_pump_energy("paris", series_id)

        # Retrieve and verify all matrices
        pl.testing.assert_frame_equal(dao.get_hydro_maxpower("paris"), dataframe, check_dtypes=False)
        pl.testing.assert_frame_equal(dao.get_hydro_reservoir("paris"), dataframe, check_dtypes=False)
        pl.testing.assert_frame_equal(dao.get_hydro_energy("paris"), dataframe, check_dtypes=False)
        pl.testing.assert_frame_equal(dao.get_hydro_run_of_river("paris"), dataframe, check_dtypes=False)
        pl.testing.assert_frame_equal(dao.get_hydro_modulation("paris"), dataframe, check_dtypes=False)
        pl.testing.assert_frame_equal(dao.get_hydro_credit_modulations("paris"), dataframe, check_dtypes=False)
        pl.testing.assert_frame_equal(dao.get_hydro_inflow_pattern("paris"), dataframe, check_dtypes=False)
        pl.testing.assert_frame_equal(dao.get_hydro_water_values("paris"), dataframe, check_dtypes=False)
        pl.testing.assert_frame_equal(dao.get_hydro_mingen("paris"), dataframe, check_dtypes=False)
        pl.testing.assert_frame_equal(dao.get_hydro_max_hourly_gen_power("paris"), dataframe, check_dtypes=False)
        pl.testing.assert_frame_equal(dao.get_hydro_max_hourly_pump_power("paris"), dataframe, check_dtypes=False)
        pl.testing.assert_frame_equal(dao.get_hydro_max_daily_gen_energy("paris"), dataframe, check_dtypes=False)
        pl.testing.assert_frame_equal(dao.get_hydro_max_daily_pump_energy("paris"), dataframe, check_dtypes=False)

        # update
        dataframe2 = pl.DataFrame(data=[[2, 3, 4], [5, 6, 7.777]], orient="row")
        series_id2 = matrix_service.create(dataframe2)
        dao.save_hydro_maxpower("paris", series_id2)
        pl.testing.assert_frame_equal(dao.get_hydro_maxpower("paris"), dataframe2, check_dtypes=False)

    def test_hydro_matrix_raises(self, dao: DatabaseStudyDao) -> None:
        """Test that get raises ValueError when area exists but matrix is not saved."""
        dao.save_area("Paris")

        getters = [
            dao.get_hydro_maxpower,
            dao.get_hydro_reservoir,
            dao.get_hydro_energy,
            dao.get_hydro_run_of_river,
            dao.get_hydro_modulation,
            dao.get_hydro_credit_modulations,
            dao.get_hydro_inflow_pattern,
            dao.get_hydro_water_values,
            dao.get_hydro_mingen,
            dao.get_hydro_max_hourly_gen_power,
            dao.get_hydro_max_hourly_pump_power,
            dao.get_hydro_max_daily_gen_energy,
            dao.get_hydro_max_daily_pump_energy,
        ]
        for getter in getters:
            # raise because no matrix is saved for area
            with pytest.raises(ValueError):
                getter("paris")
            # raise because area doesn't exist
            with pytest.raises(AreaNotFound):
                getter("nonexistent")

        savers = [
            dao.save_hydro_maxpower,
            dao.save_hydro_reservoir,
            dao.save_hydro_energy,
            dao.save_hydro_run_of_river,
            dao.save_hydro_modulation,
            dao.save_hydro_credit_modulations,
            dao.save_hydro_inflow_pattern,
            dao.save_hydro_water_values,
            dao.save_hydro_mingen,
            dao.save_hydro_max_hourly_gen_power,
            dao.save_hydro_max_hourly_pump_power,
            dao.save_hydro_max_daily_gen_energy,
            dao.save_hydro_max_daily_pump_energy,
        ]
        for saver in savers:
            with pytest.raises(AreaNotFound):
                saver("nonexistent", "some-matrix-id")

    def test_cascade_delete_hydro_matrices(self, db_session: Session, dao: DatabaseStudyDao) -> None:
        """Test that all hydro matrices are deleted when the area is deleted."""
        dao.save_area("Paris")

        matrix_service = dao._matrix_service
        series_id = matrix_service.create(pl.DataFrame(data=[[1, 2]], orient="row"))

        # Save a matrix in every table
        dao.save_hydro_maxpower("paris", series_id)
        dao.save_hydro_reservoir("paris", series_id)
        dao.save_hydro_energy("paris", series_id)
        dao.save_hydro_run_of_river("paris", series_id)
        dao.save_hydro_modulation("paris", series_id)
        dao.save_hydro_credit_modulations("paris", series_id)
        dao.save_hydro_inflow_pattern("paris", series_id)
        dao.save_hydro_water_values("paris", series_id)
        dao.save_hydro_mingen("paris", series_id)
        dao.save_hydro_max_hourly_gen_power("paris", series_id)
        dao.save_hydro_max_hourly_pump_power("paris", series_id)
        dao.save_hydro_max_daily_gen_energy("paris", series_id)
        dao.save_hydro_max_daily_pump_energy("paris", series_id)

        dao.delete_area("paris")

        with db_session:
            for table in _ALL_HYDRO_MATRIX_TABLES:
                rows = db_session.execute(select(table)).fetchall()
                assert rows == [], f"Table {table.name} should be empty after cascade delete"
