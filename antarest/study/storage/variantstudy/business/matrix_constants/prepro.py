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


def conversion() -> pl.DataFrame:
    return create_polars_dataframe([[-9999999980506447872.0, 0.0, 9999999980506447872.0], [0.0, 0.0, 0.0]])


def data() -> pl.DataFrame:
    return create_polars_dataframe([[1.0, 1.0, 0.0, 1.0, 1.0, 1.0]] * 12)
