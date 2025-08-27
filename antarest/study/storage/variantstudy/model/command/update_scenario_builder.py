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

from typing import Any, Dict, Final, List, Optional, cast

from pydantic import TypeAdapter, model_validator
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import override

from antarest.study.business.model.scenario_builder_model import Ruleset, RulesetsUpdate, update_rulesets
from antarest.study.storage.rawstudy.model.filesystem.config.scenario_builder import (
    parse_rulesets,
    parse_rulesets_update,
    serialize_rulesets,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


def _get_active_ruleset(study_data: FileStudy) -> str:
    """
    Get the active ruleset from the study data.

    The active ruleset is stored in the section "[general]" in `settings/generaldata.ini`.
    The key "active-rules-scenario" may be missing in the configuration,
    when the study is just created or when the configuration is not up-to-date.
    """
    url = ["settings", "generaldata", "general", "active-rules-scenario"]
    try:
        return cast(str, study_data.tree.get(url))
    except KeyError:
        return ""


_RULESETS_ADAPTER = TypeAdapter(RulesetsUpdate)


class UpdateScenarioBuilder(ICommand):
    """
    Command used to update a scenario builder table.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_SCENARIO_BUILDER

    # version 2: changes from dictionary representation to Ruleset class
    _SERIALIZATION_VERSION: Final[int] = 2

    # Command parameters
    # ==================

    data: RulesetsUpdate

    @model_validator(mode="before")
    @classmethod
    def _migrate_v1_to_v2(cls, values: Dict[str, Any], info: ValidationInfo) -> Dict[str, Any]:
        if info.context:
            version = info.context.version
            if version == 1:
                data = values["data"]
                rulesets = parse_rulesets_update(data)
                values["data"] = rulesets
        return values

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        """
        Apply the command to the study data.

        This method updates the current configuration of the scenario builder data.
        It adds, modifies, or removes section values based on the command's data.
        The changes are saved to the study's tree structure.

        Args:
            study_data: The study data to which the command will be applied.

        Returns:
            CommandOutput: The output of the command, indicating the status of the operation.
        """
        url = ["settings", "scenariobuilder"]

        rulesets = parse_rulesets(study_data.tree.get(url))
        update_rulesets(rulesets, self.data)

        # Ensure the active ruleset is present in the configuration.
        active_rules_scenario = _get_active_ruleset(study_data)
        if active_rules_scenario and active_rules_scenario.lower() not in {k.lower() for k in rulesets.keys()}:
            rulesets[active_rules_scenario] = Ruleset()

        study_data.tree.save(serialize_rulesets(rulesets), url)
        return command_succeeded(message="Scenario builder updated successfully")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_SCENARIO_BUILDER.value,
            version=self._SERIALIZATION_VERSION,
            args={
                "data": _RULESETS_ADAPTER.dump_python(self.data, mode="json", by_alias=True, exclude_none=True),
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
