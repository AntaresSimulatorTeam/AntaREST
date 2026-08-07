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
from dataclasses import dataclass
from typing import TypeAlias

import polars as pl


@dataclass(frozen=True)
class VariableDescription:
    name: str
    unit: str
    stat: str | None


@dataclass(frozen=True)
class OutputTable:
    columns: list[VariableDescription]
    data: pl.DataFrame


AreaOutputData: TypeAlias = OutputTable
LinkOutputData: TypeAlias = OutputTable
