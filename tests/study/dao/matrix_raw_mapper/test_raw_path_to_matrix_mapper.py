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

import numpy as np
import polars as pl
import pytest

from antarest.core.exceptions import IncorrectPathError
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.model import STUDY_VERSION_8_1
from antarest.study.storage.rawstudy.raw_path_to_matrix_mapper import RawPathToMatrixMapper
from tests.study.dao.conftest import build_db_dao, build_real_case_study


def test_get_matrix_from_path(dao_bd_930: DatabaseStudyDao, dao_fs_930: FileStudyTreeDao) -> None:
    ##########################
    # Set Up
    ##########################
    for dao in [dao_bd_930, dao_fs_930]:
        result = build_real_case_study(dao)
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

        mapper = RawPathToMatrixMapper(dao)

        load = mapper.get_matrix_from_path(Path(f"input/load/series/load_{area_id}"))
        pl.testing.assert_frame_equal(load, load_df, check_dtypes=False)

        solar = mapper.get_matrix_from_path(Path(f"input/solar/series/solar_{area_id}"))
        pl.testing.assert_frame_equal(solar, solar_df, check_dtypes=False)

        wind = mapper.get_matrix_from_path(Path(f"input/wind/series/wind_{area_id}"))
        pl.testing.assert_frame_equal(wind, wind_df, check_dtypes=False)

        misc_gen = mapper.get_matrix_from_path(Path(f"input/misc-gen/miscgen-{area_id}"))
        pl.testing.assert_frame_equal(misc_gen, misc_gen_df, check_dtypes=False)

        reserves = mapper.get_matrix_from_path(Path(f"input/reserves/{area_id}"))
        pl.testing.assert_frame_equal(reserves, reserves_df, check_dtypes=False)

        link_series = mapper.get_matrix_from_path(Path(f"input/links/{area_id}/{area2}_parameters"))
        pl.testing.assert_frame_equal(link_series, link_series_df, check_dtypes=False)

        link_direct_capacity = mapper.get_matrix_from_path(Path(f"input/links/{area_id}/capacities/{area2}_direct"))
        pl.testing.assert_frame_equal(link_direct_capacity, link_direct_df, check_dtypes=False)

        link_indirect_capacity = mapper.get_matrix_from_path(Path(f"input/links/{area_id}/capacities/{area2}_indirect"))
        pl.testing.assert_frame_equal(link_indirect_capacity, link_indirect_df, check_dtypes=False)

        thermal_prepro = mapper.get_matrix_from_path(Path(f"input/thermal/prepro/{area_id}/{thermal_id}/data"))
        pl.testing.assert_frame_equal(thermal_prepro, thermal_prepro_df, check_dtypes=False)

        thermal_modulation = mapper.get_matrix_from_path(
            Path(f"input/thermal/prepro/{area_id}/{thermal_id}/modulation")
        )
        pl.testing.assert_frame_equal(thermal_modulation, thermal_modulation_df, check_dtypes=False)

        thermal_series = mapper.get_matrix_from_path(Path(f"input/thermal/series/{area_id}/{thermal_id}/series"))
        pl.testing.assert_frame_equal(thermal_series, thermal_series_df, check_dtypes=False)

        thermal_fuel_cost = mapper.get_matrix_from_path(Path(f"input/thermal/series/{area_id}/{thermal_id}/fuelCost"))
        pl.testing.assert_frame_equal(thermal_fuel_cost, thermal_fuel_cost_df, check_dtypes=False)

        thermal_co2_cost = mapper.get_matrix_from_path(Path(f"input/thermal/series/{area_id}/{thermal_id}/CO2Cost"))
        pl.testing.assert_frame_equal(thermal_co2_cost, thermal_co2_cost_df, check_dtypes=False)

        renewable_series = mapper.get_matrix_from_path(Path(f"input/renewables/series/{area_id}/{renewable_id}/series"))
        pl.testing.assert_frame_equal(renewable_series, renewable_series_df, check_dtypes=False)

        path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/pmax_injection")
        sts_pmax_injection = mapper.get_matrix_from_path(path)
        pl.testing.assert_frame_equal(sts_pmax_injection, sts_pmax_injection_df, check_dtypes=False)

        path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/pmax_withdrawal")
        sts_pmax_withdrawal = mapper.get_matrix_from_path(path)
        pl.testing.assert_frame_equal(sts_pmax_withdrawal, sts_pmax_withdrawal_df, check_dtypes=False)

        path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/lower_rule_curve")
        sts_lower_rule_curve = mapper.get_matrix_from_path(path)
        pl.testing.assert_frame_equal(sts_lower_rule_curve, sts_lower_rule_curve_df, check_dtypes=False)

        path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/upper_rule_curve")
        sts_upper_rule_curve = mapper.get_matrix_from_path(path)
        pl.testing.assert_frame_equal(sts_upper_rule_curve, sts_upper_rule_curve_df, check_dtypes=False)

        path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/inflows")
        sts_inflows = mapper.get_matrix_from_path(path)
        pl.testing.assert_frame_equal(sts_inflows, sts_inflows_df, check_dtypes=False)

        path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/cost_injection")
        sts_cost_injection = mapper.get_matrix_from_path(path)
        pl.testing.assert_frame_equal(sts_cost_injection, sts_cost_injection_df, check_dtypes=False)

        path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/cost_withdrawal")
        sts_cost_withdrawal = mapper.get_matrix_from_path(path)
        pl.testing.assert_frame_equal(sts_cost_withdrawal, sts_cost_withdrawal_df, check_dtypes=False)

        path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/cost_level")
        sts_cost_level = mapper.get_matrix_from_path(path)
        pl.testing.assert_frame_equal(sts_cost_level, sts_cost_level_df, check_dtypes=False)

        path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/cost_variation_injection")
        sts_cost_variation_injection = mapper.get_matrix_from_path(path)
        pl.testing.assert_frame_equal(sts_cost_variation_injection, sts_cost_variation_injection_df, check_dtypes=False)

        path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/cost_variation_withdrawal")
        sts_cost_variation_withdrawal = mapper.get_matrix_from_path(path)
        pl.testing.assert_frame_equal(
            sts_cost_variation_withdrawal, sts_cost_variation_withdrawal_df, check_dtypes=False
        )

        path = Path(f"input/st-storage/constraints/{area_id}/{st_storage_id}/rhs_{constraint_id}")
        sts_constraint_matrix = mapper.get_matrix_from_path(path)
        pl.testing.assert_frame_equal(sts_constraint_matrix, sts_constraint_matrix_df, check_dtypes=False)

        hydro_maxpower = mapper.get_matrix_from_path(Path(f"input/hydro/common/capacity/maxpower_{area_id}"))
        pl.testing.assert_frame_equal(hydro_maxpower, hydro_maxpower_df, check_dtypes=False)

        hydro_reservoir = mapper.get_matrix_from_path(Path(f"input/hydro/common/capacity/reservoir_{area_id}"))
        pl.testing.assert_frame_equal(hydro_reservoir, hydro_reservoir_df, check_dtypes=False)

        hydro_energy = mapper.get_matrix_from_path(Path(f"input/hydro/prepro/{area_id}/energy"))
        pl.testing.assert_frame_equal(hydro_energy, hydro_energy_df, check_dtypes=False)

        hydro_run_of_river = mapper.get_matrix_from_path(Path(f"input/hydro/series/{area_id}/ror"))
        pl.testing.assert_frame_equal(hydro_run_of_river, hydro_run_of_river_df, check_dtypes=False)

        hydro_modulation = mapper.get_matrix_from_path(Path(f"input/hydro/series/{area_id}/mod"))
        pl.testing.assert_frame_equal(hydro_modulation, hydro_modulation_df, check_dtypes=False)

        path = Path(f"input/hydro/common/capacity/creditmodulations_{area_id}")
        hydro_credit_modulations = mapper.get_matrix_from_path(path)
        pl.testing.assert_frame_equal(hydro_credit_modulations, hydro_credit_modulations_df, check_dtypes=False)

        hydro_inflow_pattern = mapper.get_matrix_from_path(Path(f"input/hydro/common/capacity/inflowPattern_{area_id}"))
        pl.testing.assert_frame_equal(hydro_inflow_pattern, hydro_inflow_pattern_df, check_dtypes=False)

        hydro_water_values = mapper.get_matrix_from_path(Path(f"input/hydro/common/capacity/waterValues_{area_id}"))
        pl.testing.assert_frame_equal(hydro_water_values, hydro_water_values_df, check_dtypes=False)

        hydro_mingen = mapper.get_matrix_from_path(Path(f"input/hydro/series/{area_id}/mingen"))
        pl.testing.assert_frame_equal(hydro_mingen, hydro_mingen_df, check_dtypes=False)

        hydro_max_hourly_gen_power = mapper.get_matrix_from_path(
            Path(f"input/hydro/series/{area_id}/maxHourlyGenPower")
        )
        pl.testing.assert_frame_equal(hydro_max_hourly_gen_power, hydro_max_hourly_gen_power_df, check_dtypes=False)

        hydro_max_hourly_pump_power = mapper.get_matrix_from_path(
            Path(f"input/hydro/series/{area_id}/maxHourlyPumpPower")
        )
        pl.testing.assert_frame_equal(hydro_max_hourly_pump_power, hydro_max_hourly_pump_power_df, check_dtypes=False)

        path = Path(f"input/hydro/common/capacity/maxDailyGenEnergy_{area_id}")
        hydro_max_daily_gen_energy = mapper.get_matrix_from_path(path)
        pl.testing.assert_frame_equal(hydro_max_daily_gen_energy, hydro_max_daily_gen_energy_df, check_dtypes=False)

        path = Path(f"input/hydro/common/capacity/maxDailyPumpEnergy_{area_id}")
        hydro_max_daily_pump_energy = mapper.get_matrix_from_path(path)
        pl.testing.assert_frame_equal(hydro_max_daily_pump_energy, hydro_max_daily_pump_energy_df, check_dtypes=False)

        # todo: We're missing BC and Xpansion tests as they are not yet implemented in DB.


def test_save_matrix_from_path(dao_bd_930: DatabaseStudyDao) -> None:
    ##########################
    # Set Up
    ##########################
    dao = dao_bd_930
    result = build_real_case_study(dao)
    area_id, area2 = result.area1, result.area2
    thermal_id, renewable_id, st_storage_id = result.thermal_id, result.renewable_id, result.sts_id
    constraint_id = result.sts_constraint_id

    generator = np.random.default_rng(11)

    def _build_random_dataframe() -> tuple[str, pl.DataFrame]:
        matrix = pl.DataFrame(generator.integers(0, 10, size=(5, 3)), orient="row")
        matrix_id = dao._matrix_service.create(matrix)
        return matrix_id, matrix

    ##########################
    # Nominal cases
    ##########################

    mapper = RawPathToMatrixMapper(dao)

    path = Path(f"input/load/series/load_{area_id}")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_load(area_id), df, check_dtypes=False)

    path = Path(f"input/solar/series/solar_{area_id}")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_solar(area_id), df, check_dtypes=False)

    path = Path(f"input/wind/series/wind_{area_id}")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_wind(area_id), df, check_dtypes=False)

    path = Path(f"input/misc-gen/miscgen-{area_id}")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_misc_gen(area_id), df, check_dtypes=False)

    path = Path(f"input/reserves/{area_id}")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_reserves(area_id), df, check_dtypes=False)

    path = Path(f"input/links/{area_id}/{area2}_parameters")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_link_series(area_id, area2), df, check_dtypes=False)

    path = Path(f"input/links/{area_id}/capacities/{area2}_direct")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_link_direct_capacities(area_id, area2), df, check_dtypes=False)

    path = Path(f"input/links/{area_id}/capacities/{area2}_indirect")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_link_indirect_capacities(area_id, area2), df, check_dtypes=False)

    path = Path(f"input/thermal/prepro/{area_id}/{thermal_id}/data")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_thermal_prepro(area_id, thermal_id), df, check_dtypes=False)

    path = Path(f"input/thermal/prepro/{area_id}/{thermal_id}/modulation")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_thermal_modulation(area_id, thermal_id), df, check_dtypes=False)

    path = Path(f"input/thermal/series/{area_id}/{thermal_id}/series")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_thermal_series(area_id, thermal_id), df, check_dtypes=False)

    path = Path(f"input/thermal/series/{area_id}/{thermal_id}/fuelCost")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_thermal_fuel_cost(area_id, thermal_id), df, check_dtypes=False)

    path = Path(f"input/thermal/series/{area_id}/{thermal_id}/CO2Cost")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_thermal_co2_cost(area_id, thermal_id), df, check_dtypes=False)

    path = Path(f"input/renewables/series/{area_id}/{renewable_id}/series")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_renewable_series(area_id, renewable_id), df, check_dtypes=False)

    path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/pmax_injection")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_st_storage_pmax_injection(area_id, st_storage_id), df, check_dtypes=False)

    path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/pmax_withdrawal")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_st_storage_pmax_withdrawal(area_id, st_storage_id), df, check_dtypes=False)

    path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/lower_rule_curve")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_st_storage_lower_rule_curve(area_id, st_storage_id), df, check_dtypes=False)

    path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/upper_rule_curve")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_st_storage_upper_rule_curve(area_id, st_storage_id), df, check_dtypes=False)

    path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/inflows")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_st_storage_inflows(area_id, st_storage_id), df, check_dtypes=False)

    path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/cost_injection")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_st_storage_cost_injection(area_id, st_storage_id), df, check_dtypes=False)

    path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/cost_withdrawal")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_st_storage_cost_withdrawal(area_id, st_storage_id), df, check_dtypes=False)

    path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/cost_level")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_st_storage_cost_level(area_id, st_storage_id), df, check_dtypes=False)

    path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/cost_variation_injection")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(
        dao.get_st_storage_cost_variation_injection(area_id, st_storage_id), df, check_dtypes=False
    )

    path = Path(f"input/st-storage/series/{area_id}/{st_storage_id}/cost_variation_withdrawal")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(
        dao.get_st_storage_cost_variation_withdrawal(area_id, st_storage_id), df, check_dtypes=False
    )

    path = Path(f"input/st-storage/constraints/{area_id}/{st_storage_id}/rhs_{constraint_id}")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(
        dao.get_st_storage_additional_constraint_matrix(area_id, st_storage_id, constraint_id), df, check_dtypes=False
    )

    path = Path(f"input/hydro/common/capacity/maxpower_{area_id}")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_hydro_maxpower(area_id), df, check_dtypes=False)

    path = Path(f"input/hydro/common/capacity/reservoir_{area_id}")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_hydro_reservoir(area_id), df, check_dtypes=False)

    path = Path(f"input/hydro/prepro/{area_id}/energy")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_hydro_energy(area_id), df, check_dtypes=False)

    path = Path(f"input/hydro/series/{area_id}/ror")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_hydro_run_of_river(area_id), df, check_dtypes=False)

    path = Path(f"input/hydro/series/{area_id}/mod")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_hydro_modulation(area_id), df, check_dtypes=False)

    path = Path(f"input/hydro/common/capacity/creditmodulations_{area_id}")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_hydro_credit_modulations(area_id), df, check_dtypes=False)

    path = Path(f"input/hydro/common/capacity/inflowPattern_{area_id}")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_hydro_inflow_pattern(area_id), df, check_dtypes=False)

    path = Path(f"input/hydro/common/capacity/waterValues_{area_id}")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_hydro_water_values(area_id), df, check_dtypes=False)

    path = Path(f"input/hydro/series/{area_id}/mingen")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_hydro_mingen(area_id), df, check_dtypes=False)

    path = Path(f"input/hydro/series/{area_id}/maxHourlyGenPower")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_hydro_max_hourly_gen_power(area_id), df, check_dtypes=False)

    path = Path(f"input/hydro/series/{area_id}/maxHourlyPumpPower")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_hydro_max_hourly_pump_power(area_id), df, check_dtypes=False)

    path = Path(f"input/hydro/common/capacity/maxDailyGenEnergy_{area_id}")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_hydro_max_daily_gen_energy(area_id), df, check_dtypes=False)

    path = Path(f"input/hydro/common/capacity/maxDailyPumpEnergy_{area_id}")
    series_id, df = _build_random_dataframe()
    mapper.save_matrix_from_path(path, series_id)
    pl.testing.assert_frame_equal(dao.get_hydro_max_daily_pump_energy(area_id), df, check_dtypes=False)

    # todo: We're missing BC and Xpansion tests as they are not yet implemented in DB.


@pytest.mark.parametrize(
    "incorrect_path",
    [
        Path("settings/generaldata"),  # Not inside input, user or output folder
        Path("input/thermal/clusters/paris/list"),  # Not a matrix
        Path("user/my_file.xlsx"),  # Could be a matrix but not for the back-end
        Path("user/expansion/capa"),  # Folder containing matrices but not a matrix in itself
        Path(""),  # Empty path
        Path("input/wind/series/area"),  # Missing prefix
        Path("input/wind/series"),  # Folder containing matrices but not a matrix in itself
        Path("input/load/series/area"),  # Missing prefix
        Path("input/load/series"),  # Folder containing matrices but not a matrix in itself
        Path("input/solar/series/area"),  # Missing prefix
        Path("input/solar/series"),  # Folder containing matrices but not a matrix in itself
        Path("input/reserves/area/area"),  # Unexisting folder even if it starts well
        Path("input/misc-gen/area"),  # Missing prefix
        Path("input/folder"),  # Folder does not exist
        Path("input/bindingconstraints"),  # Folder containing matrices but not a matrix in itself
        Path("input/renewables/series/area/cluster/file"),  # Should end with `series`
        Path("input/renewables/prepro/area/cluster/series"),  # Should start with `series`
        Path("input/thermal/prepro/area/cluster/series"),  # Should end with `data` or `modulation`
        Path("input/thermal/series/area/cluster/file"),  # Should end with `series`, `fuelCost` or `CO2Cost`
        Path("input/links/area1/area2"),  # Should end with `_parameters`
        Path("input/links/area1/capacities/area2"),  # Should end with `_direct` or `_indirect`
        Path("input/st-storage/constraints/area/sts/c1"),  # Should end with the `rsh_` prefix
        Path("input/st-storage/series/area/sts/file"),  # Not a real matrix file even if in the right folder
        Path("input/hydro/common/capacity/file"),  # Not a real matrix file even if in the right folder
        Path("input/hydro/series/area/file"),  # Not a real matrix file even if in the right folder
    ],
)
def test_error_cases(dao_bd_930_shared: DatabaseStudyDao, incorrect_path: Path) -> None:
    mapper = RawPathToMatrixMapper(dao_bd_930_shared)

    path_pattern = incorrect_path.as_posix().replace("/", r"[\\/]")
    pattern = f"The provided path does not point to a valid matrix: '{path_pattern}'"

    with pytest.raises(IncorrectPathError, match=pattern):
        mapper.get_matrix_from_path(incorrect_path)

    with pytest.raises(IncorrectPathError, match=pattern):
        mapper.save_matrix_from_path(incorrect_path, "")


def test_version_specifics(dao_bd_930: DatabaseStudyDao) -> None:
    dao_81 = build_db_dao(dao_bd_930._db_session, dao_bd_930._matrix_service, STUDY_VERSION_8_1)
    mapper_81 = RawPathToMatrixMapper(dao_81)
    mapper_93 = RawPathToMatrixMapper(dao_bd_930)

    ##########################
    # Links
    ##########################

    # Prior to v8.2
    assert mapper_81._get_matcher(Path("input/links/france/uk"))[1].groups() == ("france", "uk")
    assert mapper_81._get_matcher(Path("input/links/france/uk_parameters"))[1].groups() == ("france", "uk_parameters")

    # After v8.2
    assert mapper_93._get_matcher(Path("input/links/france/uk_parameters"))[1].groups() == ("france", "uk")
    with pytest.raises(IncorrectPathError, match="The provided path does not point to a valid matrix"):
        mapper_93._get_matcher(Path("input/links/france/uk"))  # Missing suffix

    ##########################
    # Binding constraints
    ##########################

    # Prior to v8.7
    assert mapper_81._get_matcher(Path("input/bindingconstraints/bc1"))[1].groups() == ("bc1",)
    assert mapper_81._get_matcher(Path("input/bindingconstraints/bc1_lt"))[1].groups() == ("bc1_lt",)

    # After v8.7
    assert mapper_93._get_matcher(Path("input/bindingconstraints/bc1_lt"))[1].groups() == ("bc1",)
    with pytest.raises(IncorrectPathError, match="The provided path does not point to a valid matrix"):
        mapper_93._get_matcher(Path("input/bindingconstraints/bc1"))  # Missing suffix
