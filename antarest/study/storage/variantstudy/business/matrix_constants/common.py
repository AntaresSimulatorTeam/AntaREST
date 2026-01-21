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

from antarest.core.utils.polars import create_polars_dataframe


def null_matrix() -> pl.DataFrame:
    return pl.DataFrame()


def null_scenario_matrix() -> pl.DataFrame:
    return create_polars_dataframe([[0.0]] * 8760)


def fixed_4_columns() -> pl.DataFrame:
    return create_polars_dataframe([[0.0, 0.0, 0.0, 0.0]] * 8760)


def fixed_8_columns() -> pl.DataFrame:
    return create_polars_dataframe([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]] * 8760)


def fixed_daily_gen() -> pl.DataFrame:
    return create_polars_dataframe([[24]] * 365)


def fixed_hourly_power() -> pl.DataFrame:
    return create_polars_dataframe([[0.0]] * 8760)
