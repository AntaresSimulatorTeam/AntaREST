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
from pathlib import Path, PurePosixPath

from antarest.core.model import JSON
from antarest.study.business.study_interface import StudyInterface
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import Study, StudyMetadataDTO
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.inode import OriginalFile


class IStudyService(ABC):
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
    def get_study_dao(self, study: Study) -> StudyDao:
        raise NotImplementedError()

    @abstractmethod
    def export_study_flat(self, study: Study, dst_path: Path) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get(self, metadata: Study, url: str = "", depth: int = 3, formatted: bool = True) -> JSON:
        """
        Entry point to fetch data inside study.
        Args:
            metadata: study
            url: path data inside study to reach
            depth: tree depth to reach after reach data path
            formatted: indicate if raw files must be parsed and formatted

        Returns: study data formatted in json

        """

    @abstractmethod
    def get_file(self, metadata: Study, url: str = "") -> OriginalFile:
        """
        Entry point to fetch for a specific file inside a study folder

        Args:
            metadata: study
            url: path data inside study to reach the file

        Returns: study file content and extension

        """

    @abstractmethod
    def get_raw(
        self,
        metadata: Study,
        use_cache: bool = True,
        output_dir: Path | None = None,
    ) -> FileStudy:
        """
        Fetch a study raw tree object and its config
        Args:
            metadata: study
            use_cache: use cache
            output_dir: optional output dir override
        Returns: the config and study tree object

        """
