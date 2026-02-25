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
from pathlib import Path

import polars as pl
import pytest
from study.dao.conftest import build_real_case_db_study

from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.storage.rawstudy.raw_path_to_matrix_mapper import RawPathToMatrixMapper


def test_mapper(dao_930: DatabaseStudyDao) -> None:
    ##########################
    # Set Up
    ##########################
    result = build_real_case_db_study(dao_930)
    (
        load_df,
        solar_df,
        wind_df,
        reserves_df,
        misc_gen_df,
        link_series_df,
        link_direct_df,
        link_indirect_df,
        thermal_prepro_df,
        thermal_modulation_df,
        thermal_series_df,
        thermal_fuel_cost_df,
        thermal_co2_cost_df,
        renewable_series_df,
        sts_pmax_injection_df,
        sts_pmax_withdrawal_df,
        sts_lower_rule_curve_df,
        sts_upper_rule_curve_df,
        sts_inflows_df,
        sts_cost_injection_df,
        sts_cost_withdrawal_df,
        sts_cost_level_df,
        sts_cost_variation_injection_df,
        sts_cost_variation_withdrawal_df,
        sts_constraint_matrix_df,
        hydro_maxpower_df,
        hydro_reservoir_df,
        hydro_energy_df,
        hydro_run_of_river_df,
        hydro_modulation_df,
        hydro_credit_modulations_df,
        hydro_inflow_pattern_df,
        hydro_water_values_df,
        hydro_mingen_df,
        hydro_max_hourly_gen_power_df,
        hydro_max_hourly_pump_power_df,
        hydro_max_daily_gen_energy_df,
        hydro_max_daily_pump_energy_df,
    ) = result.dataframes
    area_id, area2 = result.area1, result.area2
    thermal_id, renewable_id, st_storage_id = result.thermal_id, result.renewable_id, result.sts_id
    constraint_id = result.sts_constraint_id

    ##########################
    # Nominal cases
    ##########################

    mapper = RawPathToMatrixMapper(dao_930)

    # Load
    load = mapper.get_matrix_from_path(Path(f"input/load/series/load_{area_id}"))
    pl.testing.assert_frame_equal(load, load_df, check_dtypes=False)

    ##########################
    # Error cases
    ##########################

    # Empty path
    with pytest.raises(ValueError, match="Path . is empty"):
        mapper.get_matrix_from_path(Path(""))

    # GeneralData
    with pytest.raises(ValueError, match='Path settings/generaldata does not point towards a matrix.'):
        mapper.get_matrix_from_path(Path("settings/generaldata"))

    # User resource
    with pytest.raises(ValueError, match='Path user/my_file.xlsx does not point towards a matrix.'):
        mapper.get_matrix_from_path(Path("user/my_file.xlsx"))

    # Thermal.ini file
    with pytest.raises(ValueError, match='Path input/thermal/clusters/paris/list does not point towards a matrix.'):
        mapper.get_matrix_from_path(Path(f"input/thermal/clusters/{area_id}/list"))
