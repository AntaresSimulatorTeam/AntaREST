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
from pathlib import Path
from typing import BinaryIO, List, Optional

from antarest.study.model import Study, StudySimResultDTO


class IOutputStorage(ABC):
    @abstractmethod
    def import_output(
        self,
        study: Study,
        output: BinaryIO | Path,
        output_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Import an output
        Args:
            study: the study
            output: Path of the output or raw data
            output_name: Optional name suffix to append to the output name
        Returns: None
        """

    @abstractmethod
    def get_study_sim_result(self, metadata: Study) -> List[StudySimResultDTO]:
        """
        Get global result information

        Args:
            metadata: study

        Returns:
            study output data
        """

    @abstractmethod
    def delete_output(self, metadata: Study, output_id: str) -> None:
        """
        Delete a simulation output
        Args:
            metadata: study
            output_id: output simulation

        Returns:

        """

    @abstractmethod
    def export_output(self, metadata: Study, output_id: str, target: Path) -> None:
        """
        Export and compresses study inside zip
        Args:
            metadata: study
            output_id: output id
            target: path of the file to export to

        Returns: zip file with study files compressed inside

        """

    @abstractmethod
    def archive_study_output(self, study: Study, output_id: str) -> bool:
        """Archive a study output."""

    # noinspection SpellCheckingInspection
    @abstractmethod
    def unarchive_study_output(self, study: Study, output_id: str, keep_src_zip: bool) -> bool:
        """Un-archive a study output."""

    @abstractmethod
    def get_output_path(self, study: Study, output_id: str) -> Path:
        """Returns the output path for the given output_id"""
