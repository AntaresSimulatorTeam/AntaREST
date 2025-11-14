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
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, List, Optional
from uuid import uuid4

from typing_extensions import override

from antarest.core.exceptions import BadOutputError
from antarest.core.utils.archives import ArchiveFormat, extract_archive
from antarest.core.utils.utils import StopWatch
from antarest.study.model import Study, StudySimResultDTO
from antarest.study.storage.utils import fix_study_root, extract_output_name

logger = logging.getLogger(__name__)


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
    def unarchive_study_output(self, study: Study, output_id: str) -> bool:
        """Un-archive a study output."""

    @abstractmethod
    def get_output_path(self, study: Study, output_id: str) -> Path:
        """Returns the output path for the given output_id"""


class OutputStorageImpl(IOutputStorage):
    @override
    def import_output(
        self,
        metadata: Study,
        output: BinaryIO | Path,
        output_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Import an output
        Args:
            output: Path of the output or raw data
            output_name: Optional name suffix to append to the output name
        Returns: None
        """
        path_output = Path(metadata.path) / "output" / f"imported_output_{str(uuid4())}"
        study_id = metadata.id
        path_output.mkdir(parents=True)
        output_full_name: Optional[str]
        is_zipped = False
        stopwatch = StopWatch()
        try:
            if isinstance(output, Path):
                if output != path_output and output.suffix != ArchiveFormat.ZIP:
                    shutil.copytree(output, path_output / "imported")
                elif output.suffix == ArchiveFormat.ZIP:
                    is_zipped = True
                    path_output.rmdir()
                    path_output = Path(str(path_output) + f"{ArchiveFormat.ZIP}")
                    shutil.copyfile(output, path_output)
            else:
                extract_archive(output, path_output)

            stopwatch.log_elapsed(lambda elapsed_time: logger.info(f"Copied output for {study_id} in {elapsed_time}s"))
            fix_study_root(path_output)
            output_full_name = extract_output_name(path_output, output_name)
            extension = f"{ArchiveFormat.ZIP}" if is_zipped else ""
            path_output = path_output.rename(Path(path_output.parent, output_full_name + extension))

            # TODO: lists content ? wtf
            data = self.get(metadata, f"output/{output_full_name}", 1, use_cache=False)

            if data is None:
                self.delete_output(metadata, "imported_output")
                raise BadOutputError("The output provided is not conform.")

        except Exception as e:
            logger.error("Failed to import output", exc_info=e)
            shutil.rmtree(path_output, ignore_errors=True)
            if is_zipped:
                Path(str(path_output) + f"{ArchiveFormat.ZIP}").unlink(missing_ok=True)
            output_full_name = None

        return output_full_name

    @override
    def get_study_sim_result(self, metadata: Study) -> List[StudySimResultDTO]:

    @override
    def delete_output(self, metadata: Study, output_id: str) -> None:


    @override
    def export_output(self, metadata: Study, output_id: str, target: Path) -> None:


    @override
    def archive_study_output(self, study: Study, output_id: str) -> bool:

    @override
    def unarchive_study_output(self, study: Study, output_id: str) -> bool:

    @override
    def get_output_path(self, study: Study, output_id: str) -> Path:
