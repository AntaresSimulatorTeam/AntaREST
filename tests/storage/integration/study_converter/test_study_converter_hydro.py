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

import polars as pl
import pytest
from sqlalchemy.orm import Session

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.config.compatibility_parameters_model import CompatibilityParameters, HydroPmax
from antarest.study.business.model.hydro_allocation_model import HydroAllocation, HydroAllocationArea
from antarest.study.business.model.hydro_correlation_model import HydroCorrelation, HydroCorrelationArea
from antarest.study.business.model.hydro_model import HydroManagement, InflowStructure
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.study_conversion.study_converter import StudyConverter
from antarest.study.model import STUDY_VERSION_8_8, STUDY_VERSION_9_2
from tests.study.dao.conftest import build_dao


def _setup_area_with_hydro(dao: DatabaseStudyDao, area_name: str) -> str:
    """Create an area with all required hydro config and matrices for conversion."""
    area_id = area_name.lower()
    dao.save_area(area_name)
    dao.save_hydro_management(HydroManagement(), area_id)
    dao.save_inflow_structure(InflowStructure(), area_id)
    dao.save_hydro_allocation(
        area_id, HydroAllocation(allocation=[HydroAllocationArea(area_id=area_id, coefficient=1)])
    )
    dao.save_hydro_correlation(
        area_id, HydroCorrelation(correlation=[HydroCorrelationArea(area_id=area_id, coefficient=100.0)])
    )

    # Required hydro matrices
    matrix = pl.DataFrame(data=[[1.0, 2.0], [3.0, 4.0]], orient="row")
    matrix_id = dao._matrix_service.create(matrix)
    dao.save_hydro_energy(area_id, matrix_id)
    dao.save_hydro_run_of_river(area_id, matrix_id)
    dao.save_hydro_modulation(area_id, matrix_id)
    dao.save_hydro_maxpower(area_id, matrix_id)
    dao.save_hydro_reservoir(area_id, matrix_id)
    dao.save_hydro_credit_modulations(area_id, matrix_id)
    dao.save_hydro_inflow_pattern(area_id, matrix_id)
    dao.save_hydro_water_values(area_id, matrix_id)
    dao.save_hydro_mingen(area_id, matrix_id)

    return area_id


class TestConvertHydroPmaxMatrices:
    """Tests for StudyConverter._convert_hydro with v9.2 pmax matrices."""

    def test_convert_hydro_with_hourly_pmax_copies_matrices(
        self, db_session: Session, matrix_service: ISimpleMatrixService
    ) -> None:
        """When source is v9.2+ with HOURLY pmax, the 4 pmax matrices should be copied."""
        source_dao = build_dao(db_session, matrix_service, STUDY_VERSION_9_2)
        target_dao = build_dao(db_session, matrix_service, STUDY_VERSION_9_2)

        area_id = _setup_area_with_hydro(source_dao, "Paris")

        # Set HOURLY pmax and save the 4 pmax matrices
        source_dao.save_compatibility_parameters(CompatibilityParameters(hydro_pmax=HydroPmax.HOURLY))

        hourly_gen = pl.DataFrame(data=[[10.0, 20.0]], orient="row")
        hourly_pump = pl.DataFrame(data=[[30.0, 40.0]], orient="row")
        daily_gen = pl.DataFrame(data=[[50.0, 60.0]], orient="row")
        daily_pump = pl.DataFrame(data=[[70.0, 80.0]], orient="row")

        source_dao.save_hydro_max_hourly_gen_power(area_id, source_dao._matrix_service.create(hourly_gen))
        source_dao.save_hydro_max_hourly_pump_power(area_id, source_dao._matrix_service.create(hourly_pump))
        source_dao.save_hydro_max_daily_gen_energy(area_id, source_dao._matrix_service.create(daily_gen))
        source_dao.save_hydro_max_daily_pump_energy(area_id, source_dao._matrix_service.create(daily_pump))

        # Prepare target area
        target_dao.save_area("Paris")

        # Run converter
        converter = StudyConverter(source_dao, target_dao, STUDY_VERSION_9_2, matrix_service)
        converter._convert_hydro(
            area_id,
            source_dao.get_all_hydro_properties()[area_id],
        )

        # Verify pmax matrices were copied
        pl.testing.assert_frame_equal(
            target_dao.get_hydro_max_hourly_gen_power(area_id), hourly_gen, check_dtypes=False
        )
        pl.testing.assert_frame_equal(
            target_dao.get_hydro_max_hourly_pump_power(area_id), hourly_pump, check_dtypes=False
        )
        pl.testing.assert_frame_equal(target_dao.get_hydro_max_daily_gen_energy(area_id), daily_gen, check_dtypes=False)
        pl.testing.assert_frame_equal(
            target_dao.get_hydro_max_daily_pump_energy(area_id), daily_pump, check_dtypes=False
        )

    def test_convert_hydro_with_daily_pmax_skips_matrices(
        self, db_session: Session, matrix_service: ISimpleMatrixService
    ) -> None:
        """When source is v9.2+ with DAILY pmax (default), no pmax matrices should be created."""
        source_dao = build_dao(db_session, matrix_service, STUDY_VERSION_9_2)
        target_dao = build_dao(db_session, matrix_service, STUDY_VERSION_9_2)

        area_id = _setup_area_with_hydro(source_dao, "Paris")

        # Default is DAILY, no pmax matrices exist in source
        target_dao.save_area("Paris")

        converter = StudyConverter(source_dao, target_dao, STUDY_VERSION_9_2, matrix_service)
        converter._convert_hydro(
            area_id,
            source_dao.get_all_hydro_properties()[area_id],
        )

        # Pmax matrices should NOT exist in target
        with pytest.raises(ValueError):
            target_dao.get_hydro_max_hourly_gen_power(area_id)
        with pytest.raises(ValueError):
            target_dao.get_hydro_max_hourly_pump_power(area_id)
        with pytest.raises(ValueError):
            target_dao.get_hydro_max_daily_gen_energy(area_id)
        with pytest.raises(ValueError):
            target_dao.get_hydro_max_daily_pump_energy(area_id)

    def test_convert_hydro_pre_v92_skips_pmax(self, db_session: Session, matrix_service: ISimpleMatrixService) -> None:
        """When source is pre-v9.2, pmax logic is skipped entirely."""
        source_dao = build_dao(db_session, matrix_service, STUDY_VERSION_8_8)
        target_dao = build_dao(db_session, matrix_service, STUDY_VERSION_8_8)

        area_id = _setup_area_with_hydro(source_dao, "Paris")
        target_dao.save_area("Paris")

        converter = StudyConverter(source_dao, target_dao, STUDY_VERSION_8_8, matrix_service)
        converter._convert_hydro(
            area_id,
            source_dao.get_all_hydro_properties()[area_id],
        )

        # Pmax matrices should NOT exist
        with pytest.raises(ValueError):
            target_dao.get_hydro_max_hourly_gen_power(area_id)
        with pytest.raises(ValueError):
            target_dao.get_hydro_max_hourly_pump_power(area_id)
        with pytest.raises(ValueError):
            target_dao.get_hydro_max_daily_gen_energy(area_id)
        with pytest.raises(ValueError):
            target_dao.get_hydro_max_daily_pump_energy(area_id)
