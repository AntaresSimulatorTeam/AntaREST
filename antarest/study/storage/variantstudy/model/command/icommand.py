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

import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import typing_extensions as te

from antarest.core.serde import AntaresBaseModel
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.dao.study_dao import StudyDao
from antarest.study.model import StudyVersionStr
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.model.command_listener.command_listener import (
    ICommandListener,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO

MATCH_SIGNATURE_SEPARATOR = "%"
logger = logging.getLogger(__name__)

# note: we ought to use a named tuple here ;-)
OutputTuple: te.TypeAlias = Tuple[CommandOutput, Dict[str, Any]]


class ICommand(ABC, AntaresBaseModel, extra="forbid", arbitrary_types_allowed=True):
    """
    Interface for all commands that can be applied to a study.

    Attributes:
        command_id: The ID of the command extracted from the database, if any.
        command_name: The name of the command.
        command_context: The context of the command.
    """

    command_id: Optional[uuid.UUID] = None
    command_name: CommandName
    command_context: CommandContext
    study_version: StudyVersionStr

    def _apply_config_dao(self, study_dao: StudyDao) -> OutputTuple:
        """
        Applies configuration changes to the study data.

        Returns:
            A tuple containing the command output and a dictionary of extra data.
        """
        return self._apply_config(study_dao.as_file_study().config)

    def _apply_dao(self, study_dao: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        """
        Applies configuration changes to the study data.

        Returns:
            A tuple containing the command output and a dictionary of extra data.
        """
        return self._apply(study_dao.as_file_study(), listener)

    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        """
        Applies configuration changes to the study data.

        Args:
            study_data: The study data configuration.

        Returns:
            A tuple containing the command output and a dictionary of extra data.
        """
        raise NotImplementedError()

    def apply_config(self, study_data: FileStudyTreeConfig) -> CommandOutput:
        """
        Applies configuration changes to the study data.

        Args:
            study_data: The study data configuration.

        Returns:
            The command output.
        """
        output, _ = self._apply_config(study_data)
        return output

    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        """
        Applies the study data to update storage configurations and saves the changes.

        Args:
            study_data: The study data to be applied.

        Returns:
            The output of the command execution.
        """
        raise NotImplementedError()

    def apply(
        self,
        study_data: StudyDao | FileStudy,
        listener: Optional[ICommandListener] = None,
    ) -> CommandOutput:
        """
        Applies the study data to update storage configurations and saves the changes.

        Args:
            study_data: The study data to be applied.
            listener: Can be used by the command to notify anyone giving one.

        Returns:
            The output of the command execution.
        """
        if isinstance(study_data, FileStudy):
            study_data = FileStudyTreeDao(study_data)
        try:
            return self._apply_dao(study_data, listener)
        except Exception as e:
            logger.warning(
                f"Failed to execute variant command {self.command_name}",
                exc_info=e,
            )
            message = f"Unexpected exception occurred when trying to apply command {self.command_name}: {e}"
            return CommandOutput(status=False, message=message)

    @abstractmethod
    def to_dto(self) -> CommandDTO:
        """
        Converts the current object to a Data Transfer Object (DTO)
        which is stored in the `CommandBlock` in the database.

        Returns:
            The DTO object representing the current command.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_inner_matrices(self) -> List[str]:
        """
        Retrieves the list of matrix IDs.
        """
        raise NotImplementedError()
