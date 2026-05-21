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

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator

from antarest.matrixstore.model import MatrixReference
from antarest.study.model import RawStudy, Study


class IStudyStorage(ABC):
    @abstractmethod
    def copy(self, src_study: Study, new_study: RawStudy) -> RawStudy:
        """
        Copies information from src_study to new_study.
        The 2 studies must have the same storage mode.
        """
        raise NotImplementedError()

    @abstractmethod
    def write_study_for_archive(self, study: RawStudy, dst_path: Path) -> None:
        raise NotImplementedError()

    @abstractmethod
    def export_study(self, study: Study, dst_path: Path) -> None:
        raise NotImplementedError()

    @abstractmethod
    def yield_matrix_references(self, study: Study) -> Iterator[MatrixReference]:
        raise NotImplementedError()

    @abstractmethod
    def get_disk_usage(self, study: Study) -> int:
        raise NotImplementedError()

    @abstractmethod
    def normalize_study(self, study: Study) -> None:
        raise NotImplementedError()

    @abstractmethod
    def import_study(self, study: RawStudy) -> None:
        raise NotImplementedError()
