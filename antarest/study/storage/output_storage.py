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
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, List, Optional

from antarest.study.model import MatrixIndex, StudyDownloadLevelDTO, StudySimResultDTO
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import DigestUI

logger = logging.getLogger(__name__)


class IOutputStorage(ABC):
    @abstractmethod
    def import_output(
        self,
        study_id: str,
        output: BinaryIO | Path,
        output_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Import an output
        Args:
            study_id: the study id
            output: Path of the output or raw data
            output_name: Optional name suffix to append to the output name
        Returns: None
        """

    @abstractmethod
    def get_study_sim_result(self, study_id: str) -> List[StudySimResultDTO]:
        """
        Get the list of output for a study
        """

    @abstractmethod
    def delete_output(self, study_id: str, output_id: str) -> None:
        """
        Delete a simulation output
        """

    @abstractmethod
    def export_output(self, study_id: str, output_id: str, target: Path) -> None:
        """
        Export and compresses study inside zip
        """

    @abstractmethod
    def archive_study_output(self, study_id: str, output_id: str) -> bool:
        """Archive a study output."""

    # noinspection SpellCheckingInspection
    @abstractmethod
    def unarchive_study_output(self, study_id: str, output_id: str) -> bool:
        """Un-archive a study output."""

    @abstractmethod
    def get_output_path(self, study_id: str, output_id: str) -> Path:
        """Returns the output path for the given output_id"""

    @abstractmethod
    def get_digest(self, study_id: str, output_id: str) -> DigestUI:
        """
        Digest of the output.
        """

    @abstractmethod
    def get_output_time_index(self, study_id: str, output_id: str, frequency: StudyDownloadLevelDTO) -> MatrixIndex:
        """
        Get the time index (start date and step count) for output matrices with a given frequency.
        Args:
            study_id: ID of the study
            output_id: ID of the output
            frequency: temporal frequency (hourly, daily, weekly, monthly, annually)
        Returns:
            MatrixIndex with start_date, steps, first_week_size and level
        """
