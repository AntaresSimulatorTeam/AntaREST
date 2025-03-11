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
from abc import ABC, abstractmethod
from typing import Sequence

from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.core.exceptions import CommandApplicationError
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class StudyInterface(ABC):
    """
    Business domain managers can read data and add commands to a study
    through this interface.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def version(self) -> StudyVersion:
        raise NotImplementedError()

    # TODO: in the end this should provide a read-only DAO which encapsulates
    #       the actual storage implementation
    @abstractmethod
    def get_files(self) -> FileStudy:
        """
        Gets the file representation of the study.

        This is meant to be a "read-only" access to the study,
        modifications should be made through commands.
        """
        raise NotImplementedError()

    @abstractmethod
    def add_commands(
        self,
        commands: Sequence[ICommand],
    ) -> None:
        """
        Adds commands to that study.
        Note that implementations are not required to actually modify the underlying file study.
        """
        raise NotImplementedError()


class FileStudyInterface(StudyInterface):
    """
    Basic implementation of study interface.
    Only used for test purposes, currently.
    """

    def __init__(self, file_study: FileStudy):
        self.file_study = file_study

    @override
    @property
    def id(self) -> str:
        return self.file_study.config.study_id

    @override
    @property
    def version(self) -> StudyVersion:
        return self.file_study.config.version

    @override
    def get_files(self) -> FileStudy:
        return self.file_study

    @override
    def add_commands(self, commands: Sequence[ICommand]) -> None:
        for command in commands:
            result = command.apply(self.file_study)
            if not result.status:
                raise CommandApplicationError(result.message)
