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

    @abstractmethod
    def get_files(self) -> FileStudy:
        raise NotImplementedError()

    @abstractmethod
    def add_commands(
        self,
        commands: Sequence[ICommand],
    ) -> None:
        raise NotImplementedError()


class StudiesRepository(ABC):

    @abstractmethod
    def get_study_interface(self, study: Study) -> StudyInterface:
        raise NotImplementedError()
