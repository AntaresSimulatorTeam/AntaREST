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
from typing import Callable

import polars as pl

from antarest.core.exceptions import IncorrectPathError
from antarest.study.business.model.xpansion_model import XpansionResourceFileType
from antarest.study.dao.api.study_dao import ReadOnlyStudyDao
from antarest.study.model import STUDY_VERSION_8_2, STUDY_VERSION_8_7


class RawPathToMatrixMapper:
    """
    Parses a given path like `input/load/series/load_area_fr` to retrieve the corresponding matrix.
    Used for studies stored in database as the notion of path no longer exists for them.
    But to ensure backward compatibility for the `raw` endpoints we still have to return the matrices.

    The long term alternative will be to create specific endpoints for each DAO method and with that we could remove
    this class.
    """

    def __init__(self, dao: ReadOnlyStudyDao) -> None:
        self._dao = dao

    def get_matrix_from_path(self, path: Path) -> pl.DataFrame:
        basic_error_msg = f"The provided path does not point to a valid matrix: '{path}'"

        parts = path.parts
        if not parts:
            raise IncorrectPathError(f"Path {path} is empty")

        prefix, rest = parts[0], parts[1:]

        if prefix == "output":
            return self._get_matrix_inside_output_folder(rest, basic_error_msg)

        if prefix == "user":
            return self._get_matrix_inside_user_dir(rest, basic_error_msg)

        if prefix == "input":
            return self._get_matrix_inside_input_folder(rest, basic_error_msg)

        raise IncorrectPathError(basic_error_msg)

    def _get_matrix_inside_user_dir(self, parts: tuple[str, ...], error_msg: str) -> pl.DataFrame:
        """The only possible matrices are expansion weights or capacities"""
        if len(parts) != 3 or parts[0] != "expansion" or parts[1] not in ["capa", "weights"]:
            raise IncorrectPathError(error_msg)

        if parts[1] == "capa":
            matrix = self._dao.get_xpansion_resource(XpansionResourceFileType.CAPACITIES, parts[2])
        else:
            matrix = self._dao.get_xpansion_resource(XpansionResourceFileType.WEIGHTS, parts[2])

        assert isinstance(matrix, pl.DataFrame)
        return matrix

    def _get_matrix_inside_output_folder(self, parts: tuple[str, ...], error_msg: str) -> pl.DataFrame:
        # todo
        raise NotImplementedError("We do not handle output files for the moment")

    def _get_matrix_inside_input_folder(self, parts: tuple[str, ...], error_msg: str) -> pl.DataFrame:
        study_version = self._dao.get_version()

        if not parts:
            raise IncorrectPathError(error_msg)

        prefix, rest = parts[0], parts[1:]
        if prefix == "wind":
            if len(rest) != 2 or rest[0] != "series" or not rest[1].startswith("wind_"):
                raise IncorrectPathError(error_msg)
            return self._dao.get_wind(rest[1].removeprefix("wind_"))

        elif prefix == "solar":
            if len(rest) != 2 or rest[0] != "series" or not rest[1].startswith("solar_"):
                raise IncorrectPathError(error_msg)
            return self._dao.get_solar(rest[1].removeprefix("solar_"))

        elif prefix == "load":
            if len(rest) != 2 or rest[0] != "series" or not rest[1].startswith("load_"):
                raise IncorrectPathError(error_msg)
            return self._dao.get_load(rest[1].removeprefix("load_"))

        elif prefix == "reserves":
            if len(rest) != 1:
                raise IncorrectPathError(error_msg)
            return self._dao.get_reserves(rest[0])

        elif prefix == "misc-gen":
            if len(rest) != 1 or not rest[0].startswith("miscgen-"):
                raise IncorrectPathError(error_msg)
            return self._dao.get_misc_gen(rest[0].removeprefix("miscgen-"))

        elif prefix == "bindingconstraints":
            if len(rest) != 1:
                raise IncorrectPathError(error_msg)
            if study_version < STUDY_VERSION_8_7:
                return self._dao.get_constraint_values_matrix(rest[0])
            # Based on the suffix we'll know which DAO method to use
            mapping: dict[str, Callable[[str], pl.DataFrame]] = {
                "lt": self._dao.get_constraint_less_term_matrix,
                "gt": self._dao.get_constraint_greater_term_matrix,
                "eq": self._dao.get_constraint_equal_term_matrix,
            }
            bc_id, suffix = rest[0][:-3], rest[0][-2:]
            if suffix in mapping:
                return mapping[suffix](bc_id)

        elif prefix == "renewables":
            if len(rest) != 4 or rest[0] != "series" or rest[3] != "series":
                raise IncorrectPathError(error_msg)
            return self._dao.get_renewable_series(rest[1], rest[2])

        elif prefix == "thermal":
            return self._get_matrix_inside_thermal_folder(rest, error_msg)

        elif prefix == "links":
            if study_version < STUDY_VERSION_8_2:
                if len(rest) != 2:
                    raise IncorrectPathError(error_msg)
                return self._dao.get_link_series(rest[0], rest[1])

            # Since v8.2 link matrices are separated in 3 different matrices, we have to determine which one was asked.
            if len(rest) == 2:
                if rest[1].endswith("_parameters"):
                    return self._dao.get_link_series(rest[0], rest[1].removesuffix("_parameters"))
            elif len(rest) == 3 and rest[1] == "capacities":
                if rest[2].endswith("_indirect"):
                    return self._dao.get_link_indirect_capacities(rest[0], rest[2].removesuffix("_indirect"))
                elif rest[2].endswith("_direct"):
                    return self._dao.get_link_direct_capacities(rest[0], rest[2].removesuffix("_direct"))

            raise IncorrectPathError(error_msg)

        elif prefix == "st-storage":
            return self._get_matrix_inside_st_storage_folder(rest, error_msg)

        elif prefix == "hydro":
            return self._get_matrix_inside_hydro_folder(rest, error_msg)

        raise IncorrectPathError(error_msg)

    def _get_matrix_inside_hydro_folder(self, parts: tuple[str, ...], error_msg: str) -> pl.DataFrame:
        if len(parts) != 3:
            raise IncorrectPathError(error_msg)

        if parts[0] == "common" and parts[1] == "capacity":
            if parts[2].startswith("maxpower_"):
                return self._dao.get_hydro_maxpower(parts[2].removeprefix("maxpower_"))
            if parts[2].startswith("reservoir_"):
                return self._dao.get_hydro_reservoir(parts[2].removeprefix("reservoir_"))
            if parts[2].startswith("creditmodulations_"):
                return self._dao.get_hydro_credit_modulations(parts[2].removeprefix("creditmodulations_"))
            if parts[2].startswith("inflowPattern_"):
                return self._dao.get_hydro_inflow_pattern(parts[2].removeprefix("inflowPattern_"))
            if parts[2].startswith("waterValues_"):
                return self._dao.get_hydro_water_values(parts[2].removeprefix("waterValues_"))
            if parts[2].startswith("maxDailyGenEnergy_"):
                return self._dao.get_hydro_max_daily_gen_energy(parts[2].removeprefix("maxDailyGenEnergy_"))
            if parts[2].startswith("maxDailyPumpEnergy_"):
                return self._dao.get_hydro_max_daily_pump_energy(parts[2].removeprefix("maxDailyPumpEnergy_"))

        if parts[0] == "series":
            area_id = parts[1]
            mapping: dict[str, Callable[[str], pl.DataFrame]] = {
                "ror": self._dao.get_hydro_run_of_river,
                "mod": self._dao.get_hydro_modulation,
                "mingen": self._dao.get_hydro_mingen,
                "maxHourlyGenPower": self._dao.get_hydro_max_hourly_gen_power,
                "maxHourlyPumpPower": self._dao.get_hydro_max_hourly_pump_power,
            }
            if parts[2] in mapping:
                return mapping[parts[2]](area_id)

        if parts[0] == "prepro" and parts[2] == "energy":
            return self._dao.get_hydro_energy(parts[1])

        raise IncorrectPathError(error_msg)

    def _get_matrix_inside_st_storage_folder(self, parts: tuple[str, ...], error_msg: str) -> pl.DataFrame:
        if len(parts) != 4:
            raise IncorrectPathError(error_msg)

        area_id, sts_id = parts[1], parts[2]

        if parts[0] == "constraints" and parts[3].startswith("rhs_"):
            return self._dao.get_st_storage_additional_constraint_matrix(area_id, sts_id, parts[3].removeprefix("rhs_"))

        if parts[0] == "series":
            mapping: dict[str, Callable[[str, str], pl.DataFrame]] = {
                "cost_variation_withdrawal": self._dao.get_st_storage_cost_variation_withdrawal,
                "cost_variation_injection": self._dao.get_st_storage_cost_variation_injection,
                "cost_level": self._dao.get_st_storage_cost_level,
                "cost_withdrawal": self._dao.get_st_storage_cost_withdrawal,
                "cost_injection": self._dao.get_st_storage_cost_injection,
                "inflows": self._dao.get_st_storage_inflows,
                "upper_rule_curve": self._dao.get_st_storage_upper_rule_curve,
                "lower_rule_curve": self._dao.get_st_storage_lower_rule_curve,
                "pmax_withdrawal": self._dao.get_st_storage_pmax_withdrawal,
                "pmax_injection": self._dao.get_st_storage_pmax_injection,
            }
            if parts[3] in mapping:
                return mapping[parts[3]](area_id, sts_id)
        raise IncorrectPathError(error_msg)

    def _get_matrix_inside_thermal_folder(self, parts: tuple[str, ...], error_msg: str) -> pl.DataFrame:
        if len(parts) != 4:
            raise IncorrectPathError(error_msg)

        area_id, thermal_id = parts[1], parts[2]

        if parts[0] == "series":
            if parts[3] == "fuelCost":
                return self._dao.get_thermal_fuel_cost(area_id, thermal_id)
            elif parts[3] == "C02Cost":
                return self._dao.get_thermal_co2_cost(area_id, thermal_id)
            elif parts[3] == "series":
                return self._dao.get_thermal_series(area_id, thermal_id)

        elif parts[0] == "prepro":
            if parts[3] == "data":
                return self._dao.get_thermal_prepro(area_id, thermal_id)
            elif parts[3] == "modulation":
                return self._dao.get_thermal_modulation(area_id, thermal_id)

        raise IncorrectPathError(error_msg)
