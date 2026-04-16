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
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from antarest.core.exceptions import IncorrectPathError
from antarest.study.business.model.binding_constraint_model import (
    BindingConstraintFrequency,
    ConstraintId,
)
from antarest.study.business.model.xpansion_model import XpansionResourceFileType
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_8_2, STUDY_VERSION_8_7, MatrixFrequency


@dataclass(frozen=True)
class RegexMatcher:
    pattern: re.Pattern[str]
    getter: Callable[..., pl.DataFrame]
    setter: Callable[..., None]
    # Allows getting a matrix frequency from a path. Used inside the GET /matrixindex endpoint.
    frequency: Callable[..., MatrixFrequency]


class RawPathToMatrixMapper:
    """
    Parses a given path like `input/load/series/load_area_fr` to retrieve the corresponding matrix.
    Used for studies stored in database as the notion of path no longer exists for them.
    But to ensure backward compatibility for the `raw` endpoints we still have to return the matrices.

    The long term alternative will be to create specific endpoints for each DAO method and with that we could remove
    this class.
    """

    def __init__(self, dao: StudyDao) -> None:
        def _save_thermal_prepro(area_id: str, thermal_id: str, series_id: str) -> None:
            dao.save_thermal_prepro({area_id: {thermal_id: series_id}})

        def _save_thermal_modulation(area_id: str, thermal_id: str, series_id: str) -> None:
            dao.save_thermal_modulation({area_id: {thermal_id: series_id}})

        def _save_thermal_series(area_id: str, thermal_id: str, series_id: str) -> None:
            dao.save_thermal_series({area_id: {thermal_id: series_id}})

        def _save_thermal_fuel_cost(area_id: str, thermal_id: str, series_id: str) -> None:
            dao.save_thermal_fuel_cost({area_id: {thermal_id: series_id}})

        def _save_thermal_co2_cost(area_id: str, thermal_id: str, series_id: str) -> None:
            dao.save_thermal_co2_cost({area_id: {thermal_id: series_id}})

        def _save_renewable_series(area_id: str, renewable_id: str, series_id: str) -> None:
            dao.save_renewable_series({area_id: {renewable_id: series_id}})

        def _save_load(area_id: str, series_id: str) -> None:
            dao.save_load({area_id: series_id})

        def _save_solar(area_id: str, series_id: str) -> None:
            dao.save_solar({area_id: series_id})

        def _save_wind(area_id: str, series_id: str) -> None:
            dao.save_wind({area_id: series_id})

        def _save_reserves(area_id: str, series_id: str) -> None:
            dao.save_reserves({area_id: series_id})

        def _save_misc_gen(area_id: str, series_id: str) -> None:
            dao.save_misc_gen({area_id: series_id})

        def _save_link_series(area_from: str, area_to: str, series_id: str) -> None:
            dao.save_link_series({(area_from, area_to): series_id})

        def _save_link_direct_capacities(area_from: str, area_to: str, series_id: str) -> None:
            dao.save_link_direct_capacities({(area_from, area_to): series_id})

        def _save_link_indirect_capacities(area_from: str, area_to: str, series_id: str) -> None:
            dao.save_link_indirect_capacities({(area_from, area_to): series_id})

        def _save_hydro_max_power(area_id: str, series_id: str) -> None:
            dao.save_hydro_maxpower({area_id: series_id})

        def _save_hydro_reservoir(area_id: str, series_id: str) -> None:
            dao.save_hydro_reservoir({area_id: series_id})

        def _save_hydro_energy(area_id: str, series_id: str) -> None:
            dao.save_hydro_energy({area_id: series_id})

        def _save_hydro_run_of_river(area_id: str, series_id: str) -> None:
            dao.save_hydro_run_of_river({area_id: series_id})

        def _save_hydro_modulation(area_id: str, series_id: str) -> None:
            dao.save_hydro_modulation({area_id: series_id})

        def _save_hydro_credit_modulations(area_id: str, series_id: str) -> None:
            dao.save_hydro_credit_modulations({area_id: series_id})

        def _save_hydro_inflow_pattern(area_id: str, series_id: str) -> None:
            dao.save_hydro_inflow_pattern({area_id: series_id})

        def _save_hydro_water_values(area_id: str, series_id: str) -> None:
            dao.save_hydro_water_values({area_id: series_id})

        def _save_hydro_mingen(area_id: str, series_id: str) -> None:
            dao.save_hydro_mingen({area_id: series_id})

        def _save_hydro_max_hourly_gen_power(area_id: str, series_id: str) -> None:
            dao.save_hydro_max_hourly_gen_power({area_id: series_id})

        def _save_hydro_max_hourly_pump_power(area_id: str, series_id: str) -> None:
            dao.save_hydro_max_hourly_pump_power({area_id: series_id})

        def _save_hydro_max_daily_gen_energy(area_id: str, series_id: str) -> None:
            dao.save_hydro_max_daily_gen_energy({area_id: series_id})

        def _save_hydro_max_daily_pump_energy(area_id: str, series_id: str) -> None:
            dao.save_hydro_max_daily_pump_energy({area_id: series_id})

        def _save_constraint_values_matrix(constraint_id: str, series_id: str) -> None:
            dao.save_constraint_values_matrix({ConstraintId(constraint_id): series_id})

        def _save_constraint_less_term_matrix(constraint_id: str, series_id: str) -> None:
            dao.save_constraint_less_term_matrix({ConstraintId(constraint_id): series_id})

        def _save_constraint_equal_term_matrix(constraint_id: str, series_id: str) -> None:
            dao.save_constraint_equal_term_matrix({ConstraintId(constraint_id): series_id})

        def _save_constraint_greater_term_matrix(constraint_id: str, series_id: str) -> None:
            dao.save_constraint_greater_term_matrix({ConstraintId(constraint_id): series_id})

        def _save_xpansion_capacity(filename: str, series_id: str) -> None:
            dao.save_xpansion_capacity({filename: series_id})

        def _save_xpansion_weight(filename: str, series_id: str) -> None:
            dao.save_xpansion_weight({filename: series_id})

        def _save_st_storage_pmax_injection(area_id: str, storage_id: str, series_id: str) -> None:
            dao.save_st_storage_pmax_injection({area_id: {storage_id: series_id}})

        def _save_st_storage_pmax_withdrawal(area_id: str, storage_id: str, series_id: str) -> None:
            dao.save_st_storage_pmax_withdrawal({area_id: {storage_id: series_id}})

        def _save_st_storage_inflows(area_id: str, storage_id: str, series_id: str) -> None:
            dao.save_st_storage_inflows({area_id: {storage_id: series_id}})

        def _save_st_storage_upper_rule_curve(area_id: str, storage_id: str, series_id: str) -> None:
            dao.save_st_storage_upper_rule_curve({area_id: {storage_id: series_id}})

        def _save_st_storage_lower_rule_curve(area_id: str, storage_id: str, series_id: str) -> None:
            dao.save_st_storage_lower_rule_curve({area_id: {storage_id: series_id}})

        def _save_st_storage_cost_withdrawal(area_id: str, storage_id: str, series_id: str) -> None:
            dao.save_st_storage_cost_withdrawal({area_id: {storage_id: series_id}})

        def _save_st_storage_cost_injection(area_id: str, storage_id: str, series_id: str) -> None:
            dao.save_st_storage_cost_injection({area_id: {storage_id: series_id}})

        def _save_st_storage_cost_level(area_id: str, storage_id: str, series_id: str) -> None:
            dao.save_st_storage_cost_level({area_id: {storage_id: series_id}})

        def _save_st_storage_cost_variation_injection(area_id: str, storage_id: str, series_id: str) -> None:
            dao.save_st_storage_cost_variation_injection({area_id: {storage_id: series_id}})

        def _save_st_storage_cost_variation_withdrawal(area_id: str, storage_id: str, series_id: str) -> None:
            dao.save_st_storage_cost_variation_withdrawal({area_id: {storage_id: series_id}})

        def _save_st_storage_constraint(area_id: str, storage_id: str, constraint_id: str, series_id: str) -> None:
            dao.save_st_storage_constraint_matrices({area_id: {storage_id: {constraint_id: series_id}}})

        def _get_binding_constraint_matrix_frequency(constraint_id: str) -> MatrixFrequency:
            time_step = dao.get_constraint(ConstraintId(constraint_id)).time_step
            match time_step:
                case BindingConstraintFrequency.HOURLY:
                    return MatrixFrequency.HOURLY
                case BindingConstraintFrequency.DAILY:
                    return MatrixFrequency.DAILY
                case BindingConstraintFrequency.WEEKLY:
                    return MatrixFrequency.DAILY  # Not a typo
                case _:
                    raise NotImplementedError(f"FrequencyExport '{time_step}' is not implemented")

        self._path_matchers = [
            RegexMatcher(
                pattern=re.compile(r"user/expansion/capa/(?P<filename>[^/]+)"),
                getter=lambda filename: dao.get_xpansion_resource(XpansionResourceFileType.CAPACITIES, filename),  # type: ignore
                setter=_save_xpansion_capacity,
                frequency=lambda **x: MatrixFrequency.HOURLY,  # No frequency -> We return the default value
            ),
            RegexMatcher(
                pattern=re.compile(r"user/expansion/weights/(?P<filename>[^/]+)"),
                getter=lambda filename: dao.get_xpansion_resource(XpansionResourceFileType.WEIGHTS, filename),  # type: ignore
                setter=_save_xpansion_weight,
                frequency=lambda **x: MatrixFrequency.HOURLY,  # No frequency -> We return the default value
            ),
            RegexMatcher(
                pattern=re.compile(r"input/load/series/load_(?P<area_id>[^/]+)"),
                getter=dao.get_load,
                setter=_save_load,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/wind/series/wind_(?P<area_id>[^/]+)"),
                getter=dao.get_wind,
                setter=_save_wind,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/solar/series/solar_(?P<area_id>[^/]+)"),
                getter=dao.get_solar,
                setter=_save_solar,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/misc-gen/miscgen-(?P<area_id>[^/]+)"),
                getter=dao.get_misc_gen,
                setter=_save_misc_gen,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/reserves/(?P<area_id>[^/]+)"),
                getter=dao.get_reserves,
                setter=_save_reserves,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/links/(?P<area_from>[^/]+)/capacities/(?P<area_to>[^/]+)_direct"),
                getter=dao.get_link_direct_capacities,
                setter=_save_link_direct_capacities,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/links/(?P<area_from>[^/]+)/capacities/(?P<area_to>[^/]+)_indirect"),
                getter=dao.get_link_indirect_capacities,
                setter=_save_link_indirect_capacities,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/thermal/prepro/(?P<area_id>[^/]+)/(?P<thermal_id>[^/]+)/data"),
                getter=dao.get_thermal_prepro,
                setter=_save_thermal_prepro,
                frequency=lambda **x: MatrixFrequency.DAILY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/thermal/prepro/(?P<area_id>[^/]+)/(?P<thermal_id>[^/]+)/modulation"),
                getter=dao.get_thermal_modulation,
                setter=_save_thermal_modulation,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/thermal/series/(?P<area_id>[^/]+)/(?P<thermal_id>[^/]+)/series"),
                getter=dao.get_thermal_series,
                setter=_save_thermal_series,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/thermal/series/(?P<area_id>[^/]+)/(?P<thermal_id>[^/]+)/fuelCost"),
                getter=dao.get_thermal_fuel_cost,
                setter=_save_thermal_fuel_cost,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/thermal/series/(?P<area_id>[^/]+)/(?P<thermal_id>[^/]+)/CO2Cost"),
                getter=dao.get_thermal_co2_cost,
                setter=_save_thermal_co2_cost,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/renewables/series/(?P<area_id>[^/]+)/(?P<renewable_id>[^/]+)/series"),
                getter=dao.get_renewable_series,
                setter=_save_renewable_series,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/pmax_injection"),
                getter=dao.get_st_storage_pmax_injection,
                setter=_save_st_storage_pmax_injection,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/pmax_withdrawal"),
                getter=dao.get_st_storage_pmax_withdrawal,
                setter=_save_st_storage_pmax_withdrawal,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(
                    r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/lower_rule_curve"
                ),
                getter=dao.get_st_storage_lower_rule_curve,
                setter=_save_st_storage_lower_rule_curve,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(
                    r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/upper_rule_curve"
                ),
                getter=dao.get_st_storage_upper_rule_curve,
                setter=_save_st_storage_upper_rule_curve,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/inflows"),
                getter=dao.get_st_storage_inflows,
                setter=_save_st_storage_inflows,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/cost_injection"),
                getter=dao.get_st_storage_cost_injection,
                setter=_save_st_storage_cost_injection,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/cost_withdrawal"),
                getter=dao.get_st_storage_cost_withdrawal,
                setter=_save_st_storage_cost_withdrawal,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/cost_level"),
                getter=dao.get_st_storage_cost_level,
                setter=_save_st_storage_cost_level,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(
                    r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/cost_variation_injection"
                ),
                getter=dao.get_st_storage_cost_variation_injection,
                setter=_save_st_storage_cost_variation_injection,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(
                    r"input/st-storage/series/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/cost_variation_withdrawal"
                ),
                getter=dao.get_st_storage_cost_variation_withdrawal,
                setter=_save_st_storage_cost_variation_withdrawal,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/common/capacity/maxpower_(?P<area_id>[^/]+)"),
                getter=dao.get_hydro_maxpower,
                setter=_save_hydro_max_power,
                frequency=lambda **x: MatrixFrequency.DAILY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/common/capacity/reservoir_(?P<area_id>[^/]+)"),
                getter=dao.get_hydro_reservoir,
                setter=_save_hydro_reservoir,
                frequency=lambda **x: MatrixFrequency.DAILY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/prepro/(?P<area_id>[^/]+)/energy"),
                getter=dao.get_hydro_energy,
                setter=_save_hydro_energy,
                frequency=lambda **x: MatrixFrequency.HOURLY,  # Weird but retro-compatible
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/series/(?P<area_id>[^/]+)/ror"),
                getter=dao.get_hydro_run_of_river,
                setter=_save_hydro_run_of_river,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/series/(?P<area_id>[^/]+)/mod"),
                getter=dao.get_hydro_modulation,
                setter=_save_hydro_modulation,
                frequency=lambda **x: MatrixFrequency.DAILY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/series/(?P<area_id>[^/]+)/mingen"),
                getter=dao.get_hydro_mingen,
                setter=_save_hydro_mingen,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/series/(?P<area_id>[^/]+)/maxHourlyGenPower"),
                getter=dao.get_hydro_max_hourly_gen_power,
                setter=_save_hydro_max_hourly_gen_power,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/series/(?P<area_id>[^/]+)/maxHourlyPumpPower"),
                getter=dao.get_hydro_max_hourly_pump_power,
                setter=_save_hydro_max_hourly_pump_power,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/common/capacity/creditmodulations_(?P<area_id>[^/]+)"),
                getter=dao.get_hydro_credit_modulations,
                setter=_save_hydro_credit_modulations,
                frequency=lambda **x: MatrixFrequency.HOURLY,  # No frequency -> We return the default value
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/common/capacity/inflowPattern_(?P<area_id>[^/]+)"),
                getter=dao.get_hydro_inflow_pattern,
                setter=_save_hydro_inflow_pattern,
                frequency=lambda **x: MatrixFrequency.DAILY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/common/capacity/waterValues_(?P<area_id>[^/]+)"),
                getter=dao.get_hydro_water_values,
                setter=_save_hydro_water_values,
                frequency=lambda **x: MatrixFrequency.DAILY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/common/capacity/maxDailyGenEnergy_(?P<area_id>[^/]+)"),
                getter=dao.get_hydro_max_daily_gen_energy,
                setter=_save_hydro_max_daily_gen_energy,
                frequency=lambda **x: MatrixFrequency.DAILY,
            ),
            RegexMatcher(
                pattern=re.compile(r"input/hydro/common/capacity/maxDailyPumpEnergy_(?P<area_id>[^/]+)"),
                getter=dao.get_hydro_max_daily_pump_energy,
                setter=_save_hydro_max_daily_pump_energy,
                frequency=lambda **x: MatrixFrequency.DAILY,
            ),
            RegexMatcher(
                pattern=re.compile(
                    r"input/st-storage/constraints/(?P<area_id>[^/]+)/(?P<storage_id>[^/]+)/rhs_(?P<constraint_id>[^/]+)"
                ),
                getter=dao.get_st_storage_additional_constraint_matrix,
                setter=_save_st_storage_constraint,
                frequency=lambda **x: MatrixFrequency.HOURLY,
            ),
        ]
        # Handle version specific patterns
        study_version = dao.get_version()
        if study_version < STUDY_VERSION_8_2:
            self._path_matchers.append(
                RegexMatcher(
                    pattern=re.compile(r"input/links/(?P<area_from>[^/]+)/(?P<area_to>[^/]+)"),
                    getter=dao.get_link_series,
                    setter=_save_link_series,
                    frequency=lambda **x: MatrixFrequency.HOURLY,
                )
            )
        else:
            self._path_matchers.append(
                RegexMatcher(
                    pattern=re.compile(r"input/links/(?P<area_from>[^/]+)/(?P<area_to>[^/]+)_parameters"),
                    getter=dao.get_link_series,
                    setter=_save_link_series,
                    frequency=lambda **x: MatrixFrequency.HOURLY,
                )
            )
        if study_version < STUDY_VERSION_8_7:
            self._path_matchers.append(
                RegexMatcher(
                    pattern=re.compile(r"input/bindingconstraints/(?P<constraint_id>[^/]+)"),
                    getter=dao.get_constraint_values_matrix,
                    setter=_save_constraint_values_matrix,
                    frequency=_get_binding_constraint_matrix_frequency,
                )
            )
        else:
            self._path_matchers.extend(
                [
                    RegexMatcher(
                        pattern=re.compile(r"input/bindingconstraints/(?P<constraint_id>[^/]+)_lt"),
                        getter=dao.get_constraint_less_term_matrix,
                        setter=_save_constraint_less_term_matrix,
                        frequency=_get_binding_constraint_matrix_frequency,
                    ),
                    RegexMatcher(
                        pattern=re.compile(r"input/bindingconstraints/(?P<constraint_id>[^/]+)_gt"),
                        getter=dao.get_constraint_greater_term_matrix,
                        setter=_save_constraint_greater_term_matrix,
                        frequency=_get_binding_constraint_matrix_frequency,
                    ),
                    RegexMatcher(
                        pattern=re.compile(r"input/bindingconstraints/(?P<constraint_id>[^/]+)_eq"),
                        getter=dao.get_constraint_equal_term_matrix,
                        setter=_save_constraint_equal_term_matrix,
                        frequency=_get_binding_constraint_matrix_frequency,
                    ),
                ]
            )

    def _get_matcher(self, path: Path) -> tuple[RegexMatcher, re.Match[str]]:
        for regex_matcher in self._path_matchers:
            match = regex_matcher.pattern.fullmatch(path.as_posix())
            if match:
                return regex_matcher, match

        raise IncorrectPathError(f"The provided path does not point to a valid matrix: '{path}'")

    def get_matrix_from_path(self, path: Path) -> pl.DataFrame:
        matcher, match = self._get_matcher(path)
        return matcher.getter(**match.groupdict())

    def save_matrix_from_path(self, path: Path, series_id: str) -> None:
        matcher, match = self._get_matcher(path)
        return matcher.setter(**{**match.groupdict(), "series_id": series_id})

    def get_matrix_frequency_from_path(self, path: Path) -> MatrixFrequency:
        matcher, match = self._get_matcher(path)
        return matcher.frequency(**match.groupdict())
