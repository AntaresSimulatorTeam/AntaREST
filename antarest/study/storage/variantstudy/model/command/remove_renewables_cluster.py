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

from typing import Any, Dict, List, Optional, Tuple

from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveRenewablesCluster(ICommand):
    """
    Command used to remove a renewable cluster in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REMOVE_RENEWABLES_CLUSTER

    # Command parameters
    # ==================

    area_id: str
    cluster_id: str

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        """
        Applies configuration changes to the study data: remove the renewable clusters from the storages list.

        Args:
            study_data: The study data configuration.

        Returns:
            A tuple containing the command output and a dictionary of extra data.
            On success, the dictionary is empty.
        """
        # Search the Area in the configuration
        if self.area_id not in study_data.areas:
            message = f"Area '{self.area_id}' does not exist in the study configuration."
            return CommandOutput(status=False, message=message), {}
        area: Area = study_data.areas[self.area_id]

        # Search the Renewable cluster in the area
        renewable = next(
            iter(renewable for renewable in area.renewables if renewable.id == self.cluster_id),
            None,
        )
        if renewable is None:
            message = f"Renewable cluster '{self.cluster_id}' does not exist in the area '{self.area_id}'."
            return CommandOutput(status=False, message=message), {}

        for renewable in area.renewables:
            if renewable.id == self.cluster_id:
                break
        else:
            message = f"Renewable cluster '{self.cluster_id}' does not exist in the area '{self.area_id}'."
            return CommandOutput(status=False, message=message), {}

        # Remove the Renewable cluster from the configuration
        area.renewables.remove(renewable)

        message = f"Renewable cluster '{self.cluster_id}' removed from the area '{self.area_id}'."
        return CommandOutput(status=True, message=message), {}

    def _remove_cluster_from_scenario_builder(self, study_data: FileStudy) -> None:
        """
        Update the scenario builder by removing the rows that correspond to the renewable cluster to remove.

        NOTE: this update can be very long if the scenario builder configuration is large.
        """
        rulesets = study_data.tree.get(["settings", "scenariobuilder"])

        for ruleset in rulesets.values():
            for key in list(ruleset):
                # The key is in the form "symbol,area,year,cluster"
                symbol, *parts = key.split(",")
                if symbol == "r" and parts[0] == self.area_id and parts[2] == self.cluster_id.lower():
                    del ruleset[key]

        study_data.tree.save(rulesets, ["settings", "scenariobuilder"])

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        """
        Applies the study data to update renewable cluster configurations and saves the changes:
        remove corresponding the configuration and remove the attached time series.

        Args:
            study_data: The study data to be applied.

        Returns:
            The output of the command execution.
        """
        # Search the Area in the configuration
        if self.area_id not in study_data.config.areas:
            message = f"Area '{self.area_id}' does not exist in the study configuration."
            return CommandOutput(status=False, message=message)

        # It is required to delete the files and folders that correspond to the renewable cluster
        # BEFORE updating the configuration, as we need the configuration to do so.
        # Specifically, deleting the time series uses the list of renewable clusters from the configuration.

        series_id = self.cluster_id.lower()
        paths = [
            ["input", "renewables", "clusters", self.area_id, "list", self.cluster_id],
            ["input", "renewables", "series", self.area_id, series_id],
        ]
        area: Area = study_data.config.areas[self.area_id]
        if len(area.renewables) == 1:
            paths.append(["input", "renewables", "series", self.area_id])

        for path in paths:
            study_data.tree.delete(path)

        self._remove_cluster_from_scenario_builder(study_data)

        # Deleting the renewable cluster in the configuration must be done AFTER
        # deleting the files and folders.
        return self._apply_config(study_data.config)[0]

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"area_id": self.area_id, "cluster_id": self.cluster_id},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
