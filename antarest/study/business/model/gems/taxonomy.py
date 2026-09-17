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

from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case


class _GemsCategories(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: str
    parent_category: str | None = None

    # These fields are not used in the current implementation
    # That's why they are treated as unknown data
    variables: str | None = None
    parameters: str | None = None
    ports: str | None = None
    extra_outputs: str | None = None
    properties: str | None = None
    binding_constraints: str | None = None


class GemsTaxonomy(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str
    description: str | None = None
    categories: list[_GemsCategories] = Field(default_factory=list)
