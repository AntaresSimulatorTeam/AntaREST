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

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.core.exceptions import (
    AreaNotFound,
    HydroConfigNotFound,
    HydroInflowStructureNotFound,
)
from antarest.study.business.model.hydro_allocation_model import HydroAllocation, HydroAllocationArea
from antarest.study.business.model.hydro_correlation_model import (
    HydroCorrelation,
    HydroCorrelationArea,
    HydroCorrelationMatrix,
)
from antarest.study.business.model.hydro_model import HydroManagement, InflowStructure
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.hydro import (
    HYDRO_ALLOCATION_TABLE,
    HYDRO_CORRELATION_TABLE,
    HYDRO_INFLOW_STRUCTURE_TABLE,
    HYDRO_MANAGEMENT_TABLE,
)


class TestHydroManagement:
    """Tests for hydro management CRUD operations."""

    def test_get_hydro_management_raises_error_for_area_without_hydro_config(self, dao: DatabaseStudyDao) -> None:
        """Test that get_hydro_management raises HydroConfigNotFound for an area without hydro config."""
        dao.save_area("Paris")

        with pytest.raises(HydroConfigNotFound):
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

        hydro_mgmt = HydroManagement(overflow_spilled_cost_difference=5.5)
        dao.save_hydro_management(hydro_mgmt, "paris")

        result = dao.get_hydro_management("paris")
        assert result.overflow_spilled_cost_difference == 5.5


class TestInflowStructure:
    """Tests for inflow structure CRUD operations."""

    def test_get_inflow_structure_raises_error_for_area_without_config(self, dao: DatabaseStudyDao) -> None:
        """Test that get_inflow_structure raises HydroInflowStructureNotFound for an area without config."""
        dao.save_area("Paris")

        with pytest.raises(HydroInflowStructureNotFound):
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

    def test_get_all_hydro_properties_raises_error_for_area_without_hydro_management(
        self, dao: DatabaseStudyDao
    ) -> None:
        """Test that get_all_hydro_properties raises HydroConfigNotFound if any area is missing hydro management."""
        dao.save_area("Paris")
        dao.save_inflow_structure(InflowStructure(inter_monthly_correlation=0.5), "paris")
        # No hydro management saved

        with pytest.raises(HydroConfigNotFound):
            dao.get_all_hydro_properties()

    def test_get_all_hydro_properties_raises_error_for_area_without_inflow_structure(
        self, dao: DatabaseStudyDao
    ) -> None:
        """Test that get_all_hydro_properties raises HydroInflowStructureNotFound if any area is missing inflow structure."""
        dao.save_area("Paris")
        dao.save_hydro_management(HydroManagement(reservoir=True), "paris")
        # No inflow structure saved

        with pytest.raises(HydroInflowStructureNotFound):
            dao.get_all_hydro_properties()

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
        """Test that get_hydro_correlation raises AreaNotFound if area doesn't exist."""
        with pytest.raises(AreaNotFound):
            dao.get_hydro_correlation("nonexistent")

    def test_save_hydro_correlation_stores_symmetric_data(self, dao: DatabaseStudyDao) -> None:
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

        correlation = HydroCorrelation(
            correlation=[
                HydroCorrelationArea(area_id="paris", coefficient=100.0),
                HydroCorrelationArea(area_id="nonexistent", coefficient=50.0),
            ]
        )
        with pytest.raises(AreaNotFound, match="nonexistent"):
            dao.save_hydro_correlation("paris", correlation)

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

        assert result.data[0][0] == 1.0
        assert result.data[0][1] == 0.6
        assert result.data[1][0] == 0.6
        assert result.data[1][1] == 1.0

        def matrix_sanity_checks(matrix: HydroCorrelationMatrix, expected_size: int) -> None:
            # Check matrix properties
            assert len(matrix.index) == expected_size
            assert len(matrix.columns) == expected_size
            assert matrix.index == matrix.columns  # Square matrix

            # Check diagonal is 1.0
            for i in range(len(matrix.index)):
                assert matrix.data[i][i] == 1.0

            # Check symmetry
            for i in range(len(matrix.index)):
                for j in range(len(matrix.columns)):
                    assert matrix.data[i][j] == matrix.data[j][i]

        matrix_sanity_checks(result, expected_size=2)

        # New area preserves matrix properties
        dao.save_area("Algiers")
        result = dao.get_hydro_correlation_matrix()
        matrix_sanity_checks(result, expected_size=3)
        assert result.data[0][0] == 1.0
        assert result.data[0][1] == 0.0
        assert result.data[0][2] == 0.0
        assert result.data[1][0] == 0.0
        assert result.data[1][1] == 1.0
        assert result.data[1][2] == 0.6
        assert result.data[2][0] == 0.0
        assert result.data[2][1] == 0.6
        assert result.data[2][2] == 1.0


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
        """Test that hydro allocation is deleted when source area is deleted."""
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

        # Delete source area
        dao.delete_area("paris")

        # Verify allocation is also deleted
        with db_session:
            stmt = select(HYDRO_ALLOCATION_TABLE).where(
                (HYDRO_ALLOCATION_TABLE.c.study_id == dao.get_study_id())
                & (HYDRO_ALLOCATION_TABLE.c.source_area_id == "paris")
            )
            rows = db_session.execute(stmt).fetchall()
            assert len(rows) == 0

    def test_cascade_delete_hydro_correlation(self, db_session: Session, dao: DatabaseStudyDao) -> None:
        """Test that hydro correlation is deleted when area is deleted."""
        dao.save_area("Paris")
        dao.save_area("London")
        dao.save_hydro_correlation(
            "paris",
            HydroCorrelation(
                correlation=[
                    HydroCorrelationArea(area_id="paris", coefficient=100.0),
                    HydroCorrelationArea(area_id="london", coefficient=50.0),
                ]
            ),
        )

        # Delete area
        dao.delete_area("paris")

        # Verify correlation is also deleted
        with db_session:
            stmt = select(HYDRO_CORRELATION_TABLE).where(
                (HYDRO_CORRELATION_TABLE.c.study_id == dao.get_study_id())
                & ((HYDRO_CORRELATION_TABLE.c.area_from == "paris") | (HYDRO_CORRELATION_TABLE.c.area_to == "paris"))
            )
            rows = db_session.execute(stmt).fetchall()
            assert len(rows) == 0
