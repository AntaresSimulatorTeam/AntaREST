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

from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import RawStudy, Study, StudyMetadataCopy, StudyMetadataDTO


class IStudyService(ABC):
    @abstractmethod
    def delete_from_filesystem(self, study: Study) -> None:
        raise NotImplementedError()

    @abstractmethod
    def copy(self, src_study: Study, metadata: StudyMetadataCopy) -> RawStudy:
        raise NotImplementedError()

    @abstractmethod
    def get_study_information(self, metadata: Study, folder_path: str | None = None) -> StudyMetadataDTO:
        raise NotImplementedError()

    @abstractmethod
    def get_study_dao(self, study: Study) -> StudyDao:
        raise NotImplementedError()

    @abstractmethod
    def export_study_flat(self, study: Study, dst_path: Path) -> None:
        raise NotImplementedError()
