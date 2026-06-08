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
from typing import BinaryIO, Iterator

from antarest.matrixstore.model import MatrixReference
from antarest.study.model import RawStudy, Study, StudyMetadataCopy


class IStudyStorage(ABC):
    @abstractmethod
    def copy(self, src_study: Study, metadata: StudyMetadataCopy) -> RawStudy:
        """Copies information from src_study to a new study according to `metadata`."""
        raise NotImplementedError()

    @abstractmethod
    def write_study_for_archive(self, study: RawStudy, dst_path: Path) -> None:
        raise NotImplementedError()

    @abstractmethod
    def unarchive(self, study: RawStudy, archive_path: Path) -> None:
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
    def import_study(self, study: RawStudy, stream: BinaryIO) -> None:
        raise NotImplementedError()
