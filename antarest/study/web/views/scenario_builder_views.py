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

"""
Adaptations of scenario builder business class for the API,
mainly for compatibility purposes.
"""

from typing import TypeAlias

from pydantic import Field

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.scenario_builder_model import (
    AreaItemsScenarios,
    AreaScenarios,
    HydroLevelsScenarios,
    Ruleset,
    Rulesets,
)


class RulesetView(AntaresBaseModel, populate_by_name=True, extra="forbid"):
    """
    The only aim of that view is to adapt aliases of a Ruleset an remove empty data,
    for API non regression.
    """

    load: AreaScenarios | None = Field(alias="l", default=None)
    thermal: AreaItemsScenarios | None = Field(alias="t", default=None)
    hydro: AreaScenarios | None = Field(alias="h", default=None)
    hydro_initial_levels: HydroLevelsScenarios | None = Field(alias="hl", default=None)
    hydro_final_levels: HydroLevelsScenarios | None = Field(alias="hfl", default=None)
    hydro_generation_power: AreaScenarios | None = Field(alias="hgp", default=None)
    wind: AreaScenarios | None = Field(alias="w", default=None)
    solar: AreaScenarios | None = Field(alias="s", default=None)
    ntc: AreaScenarios | None = Field(alias="ntc", default=None)
    renewable: AreaItemsScenarios | None = Field(alias="r", default=None)
    binding_constraints: AreaScenarios | None = Field(alias="bc", default=None)
    storage_inflows: AreaItemsScenarios | None = Field(alias="sts", default=None)

    @classmethod
    def from_model(cls, model: Ruleset) -> "RulesetView":
        field_values = {f: getattr(model, f) for f in Ruleset.model_fields.keys()}
        non_empty = {k: v for k, v in field_values.items() if v}
        return RulesetView.model_construct(**non_empty)

    def to_model(self) -> Ruleset:
        field_values = {f: getattr(self, f) for f in RulesetView.model_fields.keys()}
        for k, v in field_values.items():
            if v is None:
                field_values[k] = {}
        return Ruleset.model_construct(**field_values)


RulesetsView: TypeAlias = dict[str, RulesetView]


def rulesets_model_to_view(model: Rulesets) -> RulesetsView:
    return {name: RulesetView.from_model(m) for name, m in model.items()}


def rulesets_view_to_model(view: RulesetsView) -> Rulesets:
    return {name: v.to_model() for name, v in view.items()}
