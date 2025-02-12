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

from pydantic import Field
from typing_extensions import override

from antarest.study.model import STUDY_VERSION_8_6
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

# minimum required version.
REQUIRED_VERSION = STUDY_VERSION_8_6


class RemoveSTStorage(ICommand):
    """
    Command used to remove a short-terme storage from an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REMOVE_ST_STORAGE

    # Command parameters
    # ==================

    area_id: str = Field(description="Area ID", pattern=r"[a-z0-9_(),& -]+")
    storage_id: str = Field(description="Short term storage ID", pattern=r"[a-z0-9_(),& -]+")

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        """
        Applies configuration changes to the study data: remove the storage from the storages list.

        Args:
            study_data: The study data configuration.

        Returns:
            A tuple containing the command output and a dictionary of extra data.
            On success, the dictionary is empty.
        """
        # Check if the study version is above the minimum required version.
        version = study_data.version
        if version < REQUIRED_VERSION:
            return (
                CommandOutput(
                    status=False,
                    message=f"Invalid study version {version}, at least version {REQUIRED_VERSION} is required.",
                ),
                {},
            )

        # Search the Area in the configuration
        if self.area_id not in study_data.areas:
            return (
                CommandOutput(
                    status=False,
                    message=f"Area '{self.area_id}' does not exist in the study configuration.",
                ),
                {},
            )
        area: Area = study_data.areas[self.area_id]

        # Search the Short term storage in the area
        for st_storage in area.st_storages:
            if st_storage.id == self.storage_id:
                break
        else:
            return (
                CommandOutput(
                    status=False,
                    message=f"Short term storage '{self.storage_id}' does not exist in the area '{self.area_id}'.",
                ),
                {},
            )

        # Remove the Short term storage from the configuration
        area.st_storages.remove(st_storage)

        return (
            CommandOutput(
                status=True,
                message=f"Short term storage '{self.storage_id}' removed from the area '{self.area_id}'.",
            ),
            {},
        )

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        """
        Applies the study data to update storage configurations and saves the changes:
        remove the storage from the configuration and remove the attached time series.

        Args:
            study_data: The study data to be applied.

        Returns:
            The output of the command execution.
        """
        # It is required to delete the files and folders that correspond to the short-term storage
        # BEFORE updating the configuration, as we need the configuration to do so.
        # Specifically, deleting the time series uses the list of short-term storages from the configuration.

        paths = [
            ["input", "st-storage", "clusters", self.area_id, "list", self.storage_id],
            ["input", "st-storage", "series", self.area_id, self.storage_id],
        ]
        area: Area = study_data.config.areas[self.area_id]
        if len(area.st_storages) == 1:
            paths.append(["input", "st-storage", "series", self.area_id])

        for path in paths:
            study_data.tree.delete(path)
        # Deleting the short-term storage in the configuration must be done AFTER
        # deleting the files and folders.
        return self._apply_config(study_data.config)[0]

    @override
    def to_dto(self) -> CommandDTO:
        """
        Converts the current object to a Data Transfer Object (DTO)
        which is stored in the `CommandBlock` in the database.

        Returns:
            The DTO object representing the current command.
        """
        return CommandDTO(
            action=self.command_name.value,
            args={"area_id": self.area_id, "storage_id": self.storage_id},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
