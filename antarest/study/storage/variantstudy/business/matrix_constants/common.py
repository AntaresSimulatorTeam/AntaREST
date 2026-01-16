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


def NULL_MATRIX() -> pl.DataFrame:
    return pl.DataFrame()


def NULL_SCENARIO_MATRIX() -> pl.DataFrame:
    return create_polars_dataframe([[0.0]] * 8760)


def FIXED_4_COLUMNS() -> pl.DataFrame:
    return create_polars_dataframe([[0.0, 0.0, 0.0, 0.0]] * 8760)


def FIXED_8_COLUMNS() -> pl.DataFrame:
    return create_polars_dataframe([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]] * 8760)
