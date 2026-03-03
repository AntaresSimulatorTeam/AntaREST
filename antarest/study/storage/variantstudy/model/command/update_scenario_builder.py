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

from typing import Any, Dict, Final, Optional, Self

from pydantic import TypeAdapter, model_validator
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import override

from antarest.study.business.model.scenario_builder_model import (
    DEFAULT_RULESET_NAME,
    RulesetUpdate,
    update_ruleset,
    validate_ruleset_against_version,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.rawstudy.model.filesystem.config.scenario_builder import (
    parse_ruleset_update_from_file_data,
)
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

_RULESET_UPDATE_ADAPTER = TypeAdapter(RulesetUpdate)


class UpdateScenarioBuilder(ICommand):
    """
    Command used to update a scenario builder table.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_SCENARIO_BUILDER

    # version 2: changes from dictionary representation to Ruleset class
    # version 3: single RulesetUpdate instead of dict[str, RulesetUpdate]
    _SERIALIZATION_VERSION: Final[int] = 3

    # Command parameters
    # ==================

    data: RulesetUpdate

    @model_validator(mode="before")
    @classmethod
    def _migrate_old_versions(cls, values: Dict[str, Any], info: ValidationInfo) -> Dict[str, Any]:
        if info.context:
            version = info.context.version
            if version == 1:
                # v1: raw INI data (dict[str, RulesetFileData])
                data = values["data"]
                values["data"] = parse_ruleset_update_from_file_data(data)
            elif version == 2:
                # v2: dict[str, RulesetUpdate] — extract "Default Ruleset" or first entry
                data = values["data"]
                if isinstance(data, dict):
                    if DEFAULT_RULESET_NAME in data:
                        values["data"] = data[DEFAULT_RULESET_NAME]
                    elif data:
                        values["data"] = next(iter(data.values()))
                    else:
                        values["data"] = {}
        return values

    @model_validator(mode="after")
    def _validate_against_version(self) -> Self:
        validate_ruleset_against_version(self.study_version, self.data)
        return self

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
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
        ruleset = study_data.get_ruleset()
        update_ruleset(ruleset, self.data, self.study_version)
        study_data.save_scenario_builder(ruleset)
        return command_succeeded(message="Scenario builder updated successfully")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_SCENARIO_BUILDER.value,
            version=self._SERIALIZATION_VERSION,
            args={
                "data": _RULESET_UPDATE_ADAPTER.dump_python(self.data, mode="json", by_alias=True, exclude_none=True),
            },
            study_version=self.study_version,
        )
