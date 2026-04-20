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
from collections.abc import Sequence
from pathlib import Path, PurePosixPath

from antarest.core.exceptions import StudyNotFoundError
from antarest.study.model import Study, StudyMetadataDTO


class IStudyStorage(ABC):
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
    ) -> Study:
        """
        Create a new study by copying a reference study.

        Args:
            src_meta: The source study that you want to copy.
            dest_study_name: The name for the destination study.
            groups: A list of groups to assign to the destination study.
            destination_folder: The path where the destination study should be created. If not provided, the default path will be used.

        Returns:
            The newly created study.
        """

    @abstractmethod
    def get_study_information(self, metadata: Study, folder_path: str | None = None) -> StudyMetadataDTO:
        """Get study information.

        Args:
            metadata: The study to get information for
            folder_path: Optional pre-calculated folder path to avoid database queries
        """

    @abstractmethod
    def delete(self, metadata: Study) -> None:
        """
        Delete study
        Args:
            metadata: study

        Returns:

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
    def export_study_flat(
        self,
        metadata: Study,
        dst_path: Path,
        denormalize: bool = True,
    ) -> None:
        """
        Export study to destination

        Args:
            metadata: study.
            dst_path: destination path.
            denormalize: denormalize the study (replace matrix links by real matrices).
        """
