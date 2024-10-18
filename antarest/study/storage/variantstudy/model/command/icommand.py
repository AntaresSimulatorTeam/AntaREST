# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
import typing as t
import uuid
from abc import ABC, abstractmethod

import typing_extensions as te

from antarest.core.utils.utils import assert_this
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.core.serialization import AntaresBaseModel

if t.TYPE_CHECKING:  # False at runtime, for mypy
    from antarest.study.storage.variantstudy.business.command_extractor import CommandExtractor

MATCH_SIGNATURE_SEPARATOR = "%"
logger = logging.getLogger(__name__)

# note: we ought to use a named tuple here ;-)
OutputTuple: te.TypeAlias = t.Tuple[CommandOutput, t.Dict[str, t.Any]]


class ICommand(ABC, AntaresBaseModel, extra="forbid", arbitrary_types_allowed=True):
    """
    Interface for all commands that can be applied to a study.

    Attributes:
        command_id: The ID of the command extracted from the database, if any.
        command_name: The name of the command.
        version: The version of the command (currently always equal to 1).
        command_context: The context of the command.
    """

    command_id: t.Optional[uuid.UUID] = None
    command_name: CommandName
    version: int
    command_context: CommandContext

    @abstractmethod
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

    @abstractmethod
    def _apply(self, study_data: FileStudy) -> CommandOutput:
        """
        Applies the study data to update storage configurations and saves the changes.

        Args:
            study_data: The study data to be applied.

        Returns:
            The output of the command execution.
        """
        raise NotImplementedError()

    def apply(self, study_data: FileStudy) -> CommandOutput:
        """
        Applies the study data to update storage configurations and saves the changes.

        Args:
            study_data: The study data to be applied.

        Returns:
            The output of the command execution.
        """
        try:
            return self._apply(study_data)
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
    def match_signature(self) -> str:
        """Returns the command signature."""
        raise NotImplementedError()

    def match(self, other: "ICommand", equal: bool = False) -> bool:
        """
        Indicate if the other command is the same type and targets the same element.

        Args:
            other: other command to match against
            equal: indicate if the match must check for param equality

        Returns: True if the command match with the other else False
        """
        if not isinstance(other, self.__class__):
            return False
        excluded_fields = set(ICommand.model_fields)
        this_values = self.model_dump(exclude=excluded_fields)
        that_values = other.model_dump(exclude=excluded_fields)
        return this_values == that_values

    @abstractmethod
    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        """
        Creates a list of commands representing the differences between
        the current instance and another `ICommand` object.

        Args:
            other: Another ICommand object to compare against.

        Returns:
            A list of commands representing the differences between
            the two `ICommand` objects.
        """
        raise NotImplementedError()

    def create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        """
        Creates a list of commands representing the differences between
        the current instance and another `ICommand` object.

        Args:
            other: Another ICommand object to compare against.

        Returns:
            A list of commands representing the differences between
            the two `ICommand` objects.
        """
        assert_this(self.match(other))
        return self._create_diff(other)

    @abstractmethod
    def get_inner_matrices(self) -> t.List[str]:
        """
        Retrieves the list of matrix IDs.
        """
        raise NotImplementedError()

    def get_command_extractor(self) -> "CommandExtractor":
        """
        Create a new `CommandExtractor` used to revert the command changes.

        Returns:
            An instance of `CommandExtractor`.
        """
        from antarest.study.storage.variantstudy.business.command_extractor import CommandExtractor

        return CommandExtractor(
            self.command_context.matrix_service,
            self.command_context.patch_service,
        )
