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
from typing import BinaryIO, Optional
from uuid import uuid4

from typing_extensions import override

from antarest.core.exceptions import BadOutputError, StudyOutputNotFoundError
from antarest.core.interfaces.cache import ICache
from antarest.core.utils.archives import ArchiveFormat, archive_dir, extract_archive, unzip
from antarest.core.utils.utils import StopWatch
from antarest.study.model import StudySimResultDTO, StudySimSettingsDTO
from antarest.study.storage.output_storage import IOutputStorage
from antarest.study.storage.rawstudy.model.filesystem.config.files import get_playlist
from antarest.study.storage.rawstudy.model.filesystem.config.model import Simulation
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers
from antarest.study.storage.utils import extract_output_name, fix_study_root, remove_from_cache

logger = logging.getLogger(__name__)


class FileStudyOutputs(ABC):
    """
    The implementation based on outputs stored as files requireds the following information.

    The wiring of the application is responsible for providing a mapping from study ID to that information.
    """

    @abstractmethod
    def get_file_study(self) -> FileStudy:
        """
        Provides the "file study" form of that study.
        """

    @property
    @abstractmethod
    def outputs_path(self) -> Path:
        """
        Provides path where outputs of that file study are stored.
        """


class IFileOutputsProvider(ABC):
    """
    Responsible for mapping study ID to file output information.
    """

    @abstractmethod
    def get_outputs(self, study_id: str) -> FileStudyOutputs: ...


class OutputStorageImpl(IOutputStorage):
    def __init__(self, outputs_provider: IFileOutputsProvider, cache: ICache) -> None:
        self._outputs_provider = outputs_provider
        self._cache = cache

    @override
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
        study_outputs = self._outputs_provider.get_outputs(study_id)

        path_output = study_outputs.outputs_path / f"imported_output_{str(uuid4())}"

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
            remove_from_cache(self._cache, study_id)

            study_data = study_outputs.get_file_study()
            data = study_data.tree.get(["output", output_full_name], depth=1)

            if data is None:
                # TODO: what is that output id ??
                self.delete_output(study_id, "imported_output")
                raise BadOutputError("The output provided is not conform.")

        except Exception as e:
            logger.error("Failed to import output", exc_info=e)
            shutil.rmtree(path_output, ignore_errors=True)
            if is_zipped:
                Path(str(path_output) + f"{ArchiveFormat.ZIP}").unlink(missing_ok=True)
            output_full_name = None

        return output_full_name

    @override
    def get_study_sim_result(self, study_id: str) -> list[StudySimResultDTO]:
        """
        Get global result information

        Args:
            metadata: study

        Returns:
            study output data
        """

        study_outputs = self._outputs_provider.get_outputs(study_id)
        study_data = study_outputs.get_file_study()

        results: list[StudySimResultDTO] = []
        for output in study_data.config.outputs:
            output_data: Simulation = study_data.config.outputs[output]
            try:
                file_metadata = FileStudyHelpers.get_config(study_data, output_data.get_file())
                settings = StudySimSettingsDTO(
                    general=file_metadata["general"],
                    input=file_metadata["input"],
                    output=file_metadata["output"],
                    optimization=file_metadata["optimization"],
                    otherPreferences=file_metadata["other preferences"],
                    advancedParameters=file_metadata["advanced parameters"],
                    seedsMersenneTwister=file_metadata["seeds - Mersenne Twister"],
                    playlist=[year for year in (get_playlist(file_metadata) or {}).keys()],
                )

                results.append(
                    StudySimResultDTO(
                        name=output_data.get_file(),
                        type=output_data.mode,
                        settings=settings,
                        completionDate="",
                        status="",
                        archived=output_data.archived,
                    )
                )
            except Exception as e:
                logger.error(
                    f"Failed to retrieve info about output {output} in study {study_id}",
                    exc_info=e,
                )
        return results

    @override
    def delete_output(self, study_id: str, output_id: str) -> None:
        """
        Delete a simulation output
        Args:
            metadata: study
            output_id: output simulation

        Returns:
        """
        study_outputs = self._outputs_provider.get_outputs(study_id)
        output_path = study_outputs.outputs_path / output_id
        if output_path.exists() and output_path.is_dir():
            shutil.rmtree(output_path, ignore_errors=True)
        else:
            output_path = study_outputs.outputs_path / f"{output_id}.zip"
            output_path.unlink(missing_ok=True)
        remove_from_cache(self._cache, study_id)

    @override
    def export_output(self, study_id: str, output_id: str, target: Path) -> None:
        """
        Export and compresses study inside zip
        Args:
            output_id: output id
            target: path of the file to export to

        Returns: zip file with study files compressed inside
        """
        study_outputs = self._outputs_provider.get_outputs(study_id)

        logger.info(f"Exporting output {output_id} from study {study_id}")

        path_output = study_outputs.outputs_path / output_id
        path_output_zip = study_outputs.outputs_path / f"{output_id}{ArchiveFormat.ZIP}"

        if path_output_zip.exists():
            shutil.copyfile(path_output_zip, target)
            return None

        if not path_output.exists() and not path_output_zip.exists():
            raise StudyOutputNotFoundError()

        stopwatch = StopWatch()
        if not path_output_zip.exists():
            archive_dir(path_output, target, archive_format=ArchiveFormat.ZIP)
        stopwatch.log_elapsed(lambda x: logger.info(f"Output {output_id} from study {study_id} exported in {x}s"))

    @override
    def archive_study_output(self, study_id: str, output_id: str) -> bool:
        """Archive a study output."""
        try:
            study_outputs = self._outputs_provider.get_outputs(study_id)
            archive_dir(
                study_outputs.outputs_path / output_id,
                study_outputs.outputs_path / f"{output_id}{ArchiveFormat.ZIP}",
                remove_source_dir=True,
                archive_format=ArchiveFormat.ZIP,
            )
            remove_from_cache(self._cache, study_id)
            return True
        except Exception as e:
            logger.warning(
                f"Failed to archive study {study_id} output {output_id}",
                exc_info=e,
            )
            return False

    # noinspection SpellCheckingInspection
    @override
    def unarchive_study_output(self, study_id: str, output_id: str) -> bool:
        """Un-archive a study output."""
        study_outputs = self._outputs_provider.get_outputs(study_id)
        outputs_path = study_outputs.outputs_path
        if not (outputs_path / f"{output_id}{ArchiveFormat.ZIP}").exists():
            logger.warning(
                f"Failed to archive study {study_id} output {output_id}. Maybe it's already unarchived",
            )
            return False
        try:
            unzip(outputs_path / output_id, outputs_path / f"{output_id}{ArchiveFormat.ZIP}")
            remove_from_cache(self._cache, study_id)
            return True
        except Exception as e:
            logger.warning(
                f"Failed to unarchive study {study_id} output {output_id}",
                exc_info=e,
            )
            return False

    @override
    def get_output_path(self, study_id: str, output_id: str) -> Path:
        """Returns the output path for the given output_id"""
        study_outputs = self._outputs_provider.get_outputs(study_id)
        return study_outputs.outputs_path / output_id
