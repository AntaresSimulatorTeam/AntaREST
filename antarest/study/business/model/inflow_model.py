# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from pydantic import Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_camel_case
from antarest.study.business.all_optional_meta import all_optional_model, camel_case_model

INFLOW_PATH = ["input", "hydro", "prepro", "{area_id}", "prepro", "prepro"]


class InflowStructure(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel_case):
    """Represents the inflow structure in the hydraulic configuration."""

    inter_monthly_correlation: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="Average correlation between the energy of a month and that of the next month",
        title="Inter-monthly correlation",
    )


@all_optional_model
@camel_case_model
class InflowStructureUpdate(AntaresBaseModel, extra="forbid", populate_by_name=True):
    inter_monthly_correlation: float = Field(
        ge=0,
        le=1,
        description="Average correlation between the energy of a month and that of the next month",
        title="Inter-monthly correlation",
    )


@all_optional_model
class InflowStructureFileData(AntaresBaseModel, extra="forbid", populate_by_name=True):
    inter_monthly_correlation: float = Field(
        ge=0,
        le=1,
        alias="intermonthly-correlation",
    )
