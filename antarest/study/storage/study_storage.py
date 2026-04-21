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
from pathlib import PurePosixPath

from antarest.study.business.study_interface import StudyInterface
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import Study, StudyMetadataDTO


class IStudyStorage(ABC):
    @abstractmethod
    def get_disk_usage(self, study: Study) -> int:
        raise NotImplementedError()

    @abstractmethod
    def archive(self, study: Study) -> None:
        raise NotImplementedError()

    @abstractmethod
    def unarchive(self, study: Study) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, study: Study) -> None:
        raise NotImplementedError()

    @abstractmethod
    def copy(self, src_study: Study, dest_name: str, groups: list[str], destination_folder: PurePosixPath) -> Study:
        raise NotImplementedError()

    @abstractmethod
    def get_study_information(self, metadata: Study, folder_path: str | None = None) -> StudyMetadataDTO:
        raise NotImplementedError()

    @abstractmethod
    def get_study_interface(self, study: Study) -> StudyInterface:
        raise NotImplementedError()

    @abstractmethod
    def normalize_study(self, study: Study) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_study_dao(self, study: Study) -> StudyDao:
        raise NotImplementedError()
