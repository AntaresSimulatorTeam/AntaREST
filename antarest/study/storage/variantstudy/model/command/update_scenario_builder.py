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

from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Tuple, cast

import numpy as np
from typing_extensions import override

from antarest.core.requests import CaseInsensitiveDict
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
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


class UpdateScenarioBuilder(ICommand):
    """
    Command used to update a scenario builder table.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_SCENARIO_BUILDER

    # Command parameters
    # ==================

    data: Dict[str, Any] | Mapping[str, Any] | MutableMapping[str, Any]

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

        # NOTE: ruleset names are case-insensitive.
        curr_cfg = CaseInsensitiveDict(study_data.tree.get(url))
        for section_name, section in self.data.items():
            if section:
                curr_section = curr_cfg.setdefault(section_name, {})
                for key, value in section.items():
                    if isinstance(value, (int, float)) and not np.isnan(value):
                        curr_section[key] = value
                    else:
                        curr_section.pop(key, None)
            else:
                curr_cfg.pop(section_name, None)

        # Ensure the active ruleset is present in the configuration.
        active_rules_scenario = _get_active_ruleset(study_data)
        if active_rules_scenario:
            curr_cfg.setdefault(active_rules_scenario, {})

        # Ensure keys are sorted in each section (to improve reading performance).
        for section_name, section in curr_cfg.items():
            curr_cfg[section_name] = dict(sorted(section.items()))

        study_data.tree.save(curr_cfg, url)  # type: ignore
        return CommandOutput(status=True)

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:  # type: ignore
        pass

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_SCENARIO_BUILDER.value, args={"data": self.data}, study_version=self.study_version
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
