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
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import polars as pl

from antarest.core.exceptions import IncorrectPathError
from antarest.study.business.model.xpansion_model import XpansionResourceFileType
from antarest.study.dao.api.study_dao import StudyDao


@dataclass
class RegexMatcher:
    pattern: Any
    getter: Callable[..., pl.DataFrame]
    setter: Callable[..., None]


class RawPathToMatrixMapper:
    """
    Parses a given path like `input/load/series/load_area_fr` to retrieve the corresponding matrix.
    Used for studies stored in database as the notion of path no longer exists for them.
    But to ensure backward compatibility for the `raw` endpoints we still have to return the matrices.

    The long term alternative will be to create specific endpoints for each DAO method and with that we could remove
    this class.
    """

    def __init__(self, dao: StudyDao) -> None:
        self._dao = dao
        self._xpansion_capa_getter = lambda m: self._dao.get_xpansion_resource(XpansionResourceFileType.CAPACITIES, m)
        self._xpansion_weights_getter = lambda m: self._dao.get_xpansion_resource(XpansionResourceFileType.WEIGHTS, m)
        self._path_matchers = [
            RegexMatcher(
                pattern=re.compile(r"user/expansion/capa/(?P<file_name>[^/]+)"),
                getter=self._xpansion_capa_getter,  # type: ignore
                setter=self._dao.save_xpansion_capacity,
            ),
            RegexMatcher(
                pattern=re.compile(r"user/expansion/weights/(?P<file_name>[^/]+)"),
                getter=self._xpansion_weights_getter,  # type: ignore
                setter=self._dao.save_xpansion_weight,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/load/series/load_(?P<area_id>[^/]+)"),
                getter=self._dao.get_load,
                setter=self._dao.save_load,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/wind/series/wind_(?P<area_id>[^/]+)"),
                getter=self._dao.get_wind,
                setter=self._dao.save_wind,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/solar/series/solar_(?P<area_id>[^/]+)"),
                getter=self._dao.get_solar,
                setter=self._dao.save_solar,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/misc-gen/miscgen-(?P<area_id>[^/]+)"),
                getter=self._dao.get_misc_gen,
                setter=self._dao.save_misc_gen,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/reserves/(?P<area_id>[^/]+)"),
                getter=self._dao.get_reserves,
                setter=self._dao.save_reserves,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/links/(?P<area_from>[^/]+)/(?P<area_to>[^/]+)_parameters"),
                getter=self._dao.get_link_series,
                setter=self._dao.save_link_series,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/links/(?P<area_from>[^/]+)/capacities/(?P<area_to>[^/]+)_direct"),
                getter=self._dao.get_link_direct_capacities,
                setter=self._dao.save_link_direct_capacities,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/links/(?P<area_from>[^/]+)/capacities/(?P<area_to>[^/]+)_indirect"),
                getter=self._dao.get_link_indirect_capacities,
                setter=self._dao.save_link_indirect_capacities,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/thermal/prepro/(?P<area_id>[^/]+)/(?P<thermal_id>[^/]+)/data"),
                getter=self._dao.get_thermal_prepro,
                setter=self._dao.save_thermal_prepro,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/thermal/prepro/(?P<area_id>[^/]+)/(?P<thermal_id>[^/]+)/modulation"),
                getter=self._dao.get_thermal_modulation,
                setter=self._dao.save_thermal_modulation,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/thermal/series/(?P<area_id>[^/]+)/(?P<thermal_id>[^/]+)/series"),
                getter=self._dao.get_thermal_series,
                setter=self._dao.save_thermal_series,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/thermal/series/(?P<area_id>[^/]+)/(?P<thermal_id>[^/]+)/fuelCost"),
                getter=self._dao.get_thermal_fuel_cost,
                setter=self._dao.save_thermal_fuel_cost,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/thermal/series/(?P<area_id>[^/]+)/(?P<thermal_id>[^/]+)/CO2Cost"),
                getter=self._dao.get_thermal_co2_cost,
                setter=self._dao.save_thermal_co2_cost,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/renewables/series/(?P<area_id>[^/]+)/(?P<renewable_id>[^/]+)/series"),
                getter=self._dao.get_renewable_series,
                setter=self._dao.save_renewable_series,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/pmax_injection"),
                getter=self._dao.get_st_storage_pmax_injection,
                setter=self._dao.save_st_storage_pmax_injection,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/pmax_withdrawal"),
                getter=self._dao.get_st_storage_pmax_withdrawal,
                setter=self._dao.save_st_storage_pmax_withdrawal,
            ),
            RegexMatcher(
                pattern=re.compile(
                    r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/lower_rule_curve"
                ),
                getter=self._dao.get_st_storage_lower_rule_curve,
                setter=self._dao.save_st_storage_lower_rule_curve,
            ),
            RegexMatcher(
                pattern=re.compile(
                    r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/upper_rule_curve"
                ),
                getter=self._dao.get_st_storage_upper_rule_curve,
                setter=self._dao.save_st_storage_upper_rule_curve,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/inflows"),
                getter=self._dao.get_st_storage_inflows,
                setter=self._dao.save_st_storage_inflows,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/cost_injection"),
                getter=self._dao.get_st_storage_cost_injection,
                setter=self._dao.save_st_storage_cost_injection,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/cost_withdrawal"),
                getter=self._dao.get_st_storage_cost_withdrawal,
                setter=self._dao.save_st_storage_cost_withdrawal,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/cost_level"),
                getter=self._dao.get_st_storage_cost_level,
                setter=self._dao.save_st_storage_cost_level,
            ),
            RegexMatcher(
                pattern=re.compile(
                    r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/cost_variation_injection"
                ),
                getter=self._dao.get_st_storage_cost_variation_injection,
                setter=self._dao.save_st_storage_cost_variation_injection,
            ),
            RegexMatcher(
                pattern=re.compile(
                    r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/cost_variation_withdrawal"
                ),
                getter=self._dao.get_st_storage_cost_variation_withdrawal,
                setter=self._dao.save_st_storage_cost_variation_withdrawal,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/common/capacity/maxpower_(?P<area_id>[^/]+)"),
                getter=self._dao.get_hydro_maxpower,
                setter=self._dao.save_hydro_maxpower,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/common/capacity/reservoir_(?P<area_id>[^/]+)"),
                getter=self._dao.get_hydro_reservoir,
                setter=self._dao.save_hydro_reservoir,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/prepro/(?P<area_id>[^/]+)/energy"),
                getter=self._dao.get_hydro_energy,
                setter=self._dao.save_hydro_energy,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/series/(?P<area_id>[^/]+)/ror"),
                getter=self._dao.get_hydro_run_of_river,
                setter=self._dao.save_hydro_run_of_river,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/series/(?P<area_id>[^/]+)/mod"),
                getter=self._dao.get_hydro_modulation,
                setter=self._dao.save_hydro_modulation,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/series/(?P<area_id>[^/]+)/mingen"),
                getter=self._dao.get_hydro_mingen,
                setter=self._dao.save_hydro_mingen,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/series/(?P<area_id>[^/]+)/maxHourlyGenPower"),
                getter=self._dao.get_hydro_max_hourly_gen_power,
                setter=self._dao.save_hydro_max_hourly_gen_power,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/series/(?P<area_id>[^/]+)/maxHourlyPumpPower"),
                getter=self._dao.get_hydro_max_hourly_pump_power,
                setter=self._dao.save_hydro_max_hourly_pump_power,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/common/capacity/creditmodulations_(?P<area_id>[^/]+)"),
                getter=self._dao.get_hydro_credit_modulations,
                setter=self._dao.save_hydro_credit_modulations,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/common/capacity/inflowPattern_(?P<area_id>[^/]+)"),
                getter=self._dao.get_hydro_inflow_pattern,
                setter=self._dao.save_hydro_inflow_pattern,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/common/capacity/waterValues_(?P<area_id>[^/]+)"),
                getter=self._dao.get_hydro_water_values,
                setter=self._dao.save_hydro_water_values,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/common/capacity/maxDailyGenEnergy_(?P<area_id>[^/]+)"),
                getter=self._dao.get_hydro_max_daily_gen_energy,
                setter=self._dao.save_hydro_max_daily_gen_energy,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/common/capacity/maxDailyPumpEnergy_(?P<area_id>[^/]+)"),
                getter=self._dao.get_hydro_max_daily_pump_energy,
                setter=self._dao.save_hydro_max_daily_pump_energy,
            ),
            RegexMatcher(
                pattern=re.compile(
                    r"input/st-storage/constraints/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/rhs_(?P<constraint_id>[^/]+)"
                ),
                getter=self._dao.get_st_storage_additional_constraint_matrix,
                setter=self._dao.save_st_storage_constraint_matrix,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/bindingconstraints/(?P<constraint_id>[^/]+)"),
                getter=self._dao.get_constraint_values_matrix,
                setter=self._dao.save_constraint_values_matrix,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/bindingconstraints/(?P<constraint_id>[^/]+)_lt"),
                getter=self._dao.get_constraint_less_term_matrix,
                setter=self._dao.save_constraint_less_term_matrix,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/bindingconstraints/(?P<constraint_id>[^/]+)_gt"),
                getter=self._dao.get_constraint_greater_term_matrix,
                setter=self._dao.save_constraint_greater_term_matrix,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/bindingconstraints/(?P<constraint_id>[^/]+)_eq"),
                getter=self._dao.get_constraint_equal_term_matrix,
                setter=self._dao.save_constraint_equal_term_matrix,
            ),
        ]

    def get_matrix_from_path(self, path: Path) -> pl.DataFrame:
        # todo: we do not support outputs matrices for the moment

        for regex_matcher in self._path_matchers:
            match = regex_matcher.pattern.fullmatch(path.as_posix())
            if match:
                return regex_matcher.getter(**match.groupdict())

        raise IncorrectPathError(f"The provided path does not point to a valid matrix: '{path}'")

    def save_matrix_from_path(self, path: Path, series_id: str) -> None:
        for regex_matcher in self._path_matchers:
            match = regex_matcher.pattern.fullmatch(path.as_posix())
            if match:
                return regex_matcher.setter(**{**match.groupdict(), "series_id": series_id})

        raise IncorrectPathError(f"The provided path does not point to a valid matrix: '{path}'")
