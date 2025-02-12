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

from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class StudyInterface(ABC):
    """
    Business domain managers can read data and add commands to a study
    through this interface.
    """

    # TODO: in the end this should provide a read-only DAO which encapsulates
    #       the actual storage implementation
    @abstractmethod
    def get_files(self) -> FileStudy:
        """
        Gets the file representation of the study.
        Expected to return the same object on subsequent calls.

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
