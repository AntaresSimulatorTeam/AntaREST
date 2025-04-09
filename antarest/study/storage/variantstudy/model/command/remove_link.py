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

from typing import List, Optional

from pydantic import field_validator, model_validator
from typing_extensions import override

from antarest.study.model import STUDY_VERSION_8_2
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveLink(ICommand):
    """
    Command used to remove a link.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REMOVE_LINK

    # Command parameters
    # ==================

    # Properties of the `REMOVE_LINK` command:
    area1: str
    area2: str

    # noinspection PyMethodParameters
    @field_validator("area1", "area2", mode="before")
    def _validate_id(cls, area: str) -> str:
        if isinstance(area, str):
            # Area IDs must be in lowercase and not empty.
            area_id = transform_name_to_id(area, lower=True)
            if area_id:
                return area_id
            # Valid characters are `[a-zA-Z0-9_(),& -]` (including space).
            raise ValueError(f"Invalid area '{area}': it must not be empty or contain invalid characters")

        # Delegates the validation to Pydantic validators (e.g: type checking).
        return area

    # noinspection PyMethodParameters
    @model_validator(mode="after")
    def _validate_link(self) -> "RemoveLink":
        # By convention, the source area is always the smallest one (in lexicographic order).
        if self.area1 > self.area2:
            self.area1, self.area2 = self.area2, self.area1
        return self

    def _check_link_exists(self, study_cfg: FileStudyTreeConfig) -> CommandOutput:
        """
        Check if the source and target areas exist in the study configuration, and if a link between them exists.

        Args:
            study_cfg: The study configuration to check for the link.

        Returns:
            - The ``CommandOutput`` object indicates the status of the operation and a message.
            - The dictionary contains the source and target areas if the link exists.
        """
        status = False
        if self.area1 not in study_cfg.areas:
            message = f"The source area '{self.area1}' does not exist."
        elif self.area2 not in study_cfg.areas:
            message = f"The target area '{self.area2}' does not exist."
        elif self.area2 not in study_cfg.areas[self.area1].links:
            message = f"The link between {self.area1} and {self.area2} does not exist."
        else:
            message = f"Link between {self.area1} and {self.area2} removed"
            status = True

        return CommandOutput(status=status, message=message)

    def remove_from_config(self, study_cfg: FileStudyTreeConfig) -> CommandOutput:
        """
        Update the study configuration by removing the link between the source and target areas.

        Args:
            study_cfg: The study configuration to update.

        Returns:
            A tuple containing the command output and a dictionary of extra data.
            On success, the dictionary contains the source and target areas.
        """
        output = self._check_link_exists(study_cfg)

        if output.status:
            del study_cfg.areas[self.area1].links[self.area2]

        return output

    def _remove_link_from_scenario_builder(self, study_data: FileStudy) -> None:
        """
        Update the scenario builder by removing the rows that correspond to the link to remove.

        NOTE: this update can be very long if the scenario builder configuration is large.
        """
        rulesets = study_data.tree.get(["settings", "scenariobuilder"])

        for ruleset in rulesets.values():
            for key in list(ruleset):
                # The key is in the form "symbol,area1,area2,year".
                symbol, *parts = key.split(",")
                if symbol == "ntc" and parts[0] == self.area1 and parts[1] == self.area2:
                    del ruleset[key]

        study_data.tree.save(rulesets, ["settings", "scenariobuilder"])

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        """
        Update the configuration and the study data by removing the link between the source and target areas.

        Args:
            study_data (FileStudy): The study data from which the link will be removed.

        Returns:
            The status of the operation and a message.
        """

        output = self._check_link_exists(study_data.config)

        if output.status:
            if study_data.config.version < STUDY_VERSION_8_2:
                study_data.tree.delete(["input", "links", self.area1, self.area2])
            else:
                study_data.tree.delete(["input", "links", self.area1, f"{self.area2}_parameters"])
                study_data.tree.delete(["input", "links", self.area1, "capacities", f"{self.area2}_direct"])
                study_data.tree.delete(["input", "links", self.area1, "capacities", f"{self.area2}_indirect"])
            study_data.tree.delete(["input", "links", self.area1, "properties", self.area2])

            self._remove_link_from_scenario_builder(study_data)

        return self.remove_from_config(study_data.config)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_LINK.value,
            args={"area1": self.area1, "area2": self.area2},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
