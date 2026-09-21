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

from typing import Annotated

from pydantic import ConfigDict, Field, NonNegativeInt, PositiveInt, StringConstraints

from antarest.core.serde import AntaresBaseModel

ScenarioGroupId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, pattern=r"^[^,=\r\n]+$")]
ScenarioMapping = Annotated[dict[NonNegativeInt, PositiveInt], Field(min_length=1)]


class GemsScenarioBuilder(AntaresBaseModel):
    """Map each group's zero-based scenarios to one-based data-series columns."""

    model_config = ConfigDict(extra="forbid")

    scenario_groups: dict[ScenarioGroupId, ScenarioMapping] = Field(default_factory=dict)
