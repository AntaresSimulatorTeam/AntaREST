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
from pathlib import Path, PurePosixPath
from typing import List, Optional, Sequence

from antarest.core.exceptions import StudyNotFoundError
from antarest.core.model import JSON
from antarest.study.model import Study, StudyMetadataDTO
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfigDTO
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.inode import OriginalFile


class IStudyStorage(ABC):
    @abstractmethod
    def create(self, metadata: Study) -> Study:
        """
        Create empty new study
        Args:
            metadata: study information

        Returns: new study information

        """

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
    def exists(self, metadata: Study) -> bool:
        """
        Check study exist.
        Args:
            metadata: study

        Returns: true if study presents in disk, false else.

        """

    @abstractmethod
    def copy(
        self,
        src_meta: Study,
        dest_study_name: str,
        groups: Sequence[str],
        destination_folder: PurePosixPath,
        output_ids: List[str],
        with_outputs: bool | None,
        editor: str,
    ) -> Study:
        """
        Create a new study by copying a reference study.

        Args:
            src_meta: The source study that you want to copy.
            dest_study_name: The name for the destination study.
            groups: A list of groups to assign to the destination study.
            destination_folder: The path where the destination study should be created. If not provided, the default path will be used.
            output_ids: A list of output names that you want to include in the destination study.
            with_outputs: Indicates whether to copy the outputs as well.
            editor: The name of the editor that should be assigned to the destination study.

        Returns:
            The newly created study.
        """

    @abstractmethod
    def get_study_information(self, metadata: Study) -> StudyMetadataDTO:
        """Get study information."""

    @abstractmethod
    def get_raw(
        self,
        metadata: Study,
        use_cache: bool = True,
        output_dir: Optional[Path] = None,
    ) -> FileStudy:
        """
        Fetch a study raw tree object and its config
        Args:
            metadata: study
            use_cache: use cache
            output_dir: optional output dir override
        Returns: the config and study tree object

        """

    @abstractmethod
    def delete(self, metadata: Study) -> None:
        """
        Delete study
        Args:
            metadata: study

        Returns:

        """

    @abstractmethod
    def get_study_path(self, metadata: Study) -> Path:
        """
        Get study path
        Args:
            metadata: study information

        Returns: study path

        """

    def _check_study_exists(self, metadata: Study) -> None:
        """
        Check study on filesystem.

        Args:
            metadata: study

        Returns: none or raise error if not found

        """
        if not self.exists(metadata):
            raise StudyNotFoundError(f"Study with the uuid {metadata.id} does not exist.")

    @abstractmethod
    def export_study(self, metadata: Study, target: Path, outputs: bool = True) -> Path:
        """
        Export and compress a study to a ZIP file.

        Args:
            metadata: The study metadata.
            target: The path of the ZIP file to export to.
            outputs: Whether to include the output folder inside the exportation.

        Returns:
            Path: The path to the created ZIP file containing the study files.
        """

    @abstractmethod
    def export_study_flat(
        self,
        metadata: Study,
        dst_path: Path,
        outputs: bool = True,
        output_list_filter: Optional[List[str]] = None,
        denormalize: bool = True,
    ) -> None:
        """
        Export study to destination

        Args:
            metadata: study.
            dst_path: destination path.
            outputs: list of outputs to keep.
            output_list_filter: list of outputs to keep (None indicate all outputs).
            denormalize: denormalize the study (replace matrix links by real matrices).
        """

    @abstractmethod
    def get_synthesis(self, metadata: Study) -> FileStudyTreeConfigDTO:
        """
        Return study synthesis
        Args:
            metadata: study
        Returns: FileStudyTreeConfigDTO

        """

    @abstractmethod
    def initialize_additional_data(self, study: Study) -> bool:
        """Initialize additional data for a study."""
