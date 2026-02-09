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
import uuid
from pathlib import Path
from typing import BinaryIO, Iterator, List, Optional, Sequence

import pandas as pd
from typing_extensions import override

from antarest.core.exceptions import OutputNotFound
from antarest.core.utils.archives import ArchiveFormat, archive_dir, extract_archive
from antarest.core.utils.utils import StopWatch
from antarest.study.model import MatrixFrequency, MatrixIndex, StudySimResultDTO, StudySimSettingsDTO
from antarest.study.output.filestudy.extract_metadata import extract_metadata
from antarest.study.output.lfs.lfs import ILargeFileStorage
from antarest.study.output.output_model import OutputVariablesList
from antarest.study.output.output_storage import BasicOutputMetadata, IOutputStorage, OutputStorageType
from antarest.study.output.storage.repository import OutputMetadata, OutputMetadataRepository
from antarest.study.output.utils import QueryFileType
from antarest.study.storage.rawstudy.model.filesystem.config.model import Simulation
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import DigestUI
from antarest.study.storage.utils import extract_output_name, fix_study_root

logger = logging.getLogger(__name__)


def _archive_id(study_id: str, output_name: str) -> str:
    # TODO: use a UUID stored in DB instead ?
    return f"{study_id}-{output_name}"


def _empty_settings() -> StudySimSettingsDTO:
    return StudySimSettingsDTO(
        general={},
        input={},
        output={},
        optimization={},
        otherPreferences={},
        advancedParameters={},
        seedsMersenneTwister={},
    )


def _metadata_to_sim_result(metadata: OutputMetadata) -> StudySimResultDTO:
    return StudySimResultDTO(
        archived=metadata.archived,
        name=metadata.output_name,
        settings=_empty_settings(),  # TODO
        completionDate="",
        status="",
        type=metadata.type,
    )


def _write_temporary_files(tmp_dir: Path, output: BinaryIO | Path) -> tuple[Path, Path]:
    """
    Ensures we have the output in both forms on disk, compressed and uncompressed,
    whatever the input is (a compressed binary stream, or a compressed or uncompressed path).

    Returns:
        the path to the compressed archive, and the path to the uncompressed directory.
    """
    archive_path = tmp_dir / f"{uuid.uuid4()}"
    dir_path = tmp_dir / f"{uuid.uuid4()}"
    try:
        if isinstance(output, Path):
            if output.is_dir():
                shutil.copytree(output, dir_path, dirs_exist_ok=False)
                archive_path = tmp_dir / f"{uuid.uuid4()}{ArchiveFormat.ZIP}"
                archive_dir(dir_path, archive_path, remove_source_dir=False, archive_format=ArchiveFormat.ZIP)
            else:
                shutil.copy(output, archive_path)
                with archive_path.open("rb") as f:
                    extract_archive(f, dir_path)
        else:
            # write the archive to one dir and extract to the second
            with archive_path.open("wb") as f:
                shutil.copyfileobj(output, f)
            with archive_path.open("rb") as f:
                extract_archive(f, dir_path)

        # Still needed to ensure the output is not in a sub-directory
        fix_study_root(dir_path)
    except Exception:
        shutil.rmtree(archive_path, ignore_errors=True)
        shutil.rmtree(dir_path, ignore_errors=True)
        raise
    return archive_path, dir_path


class V2OutputStorage(IOutputStorage):
    """
    The implementation will be based on a few sub-components:
    - archives will be stored in an LFS
    - metadata will be stored in database
    - actual variables values will be unarchived to parquet files

    The tmp directory will be used on import or unarchival to store uncompressed files.
    """

    def __init__(
        self, tmp_dir: Path, metadata_repository: OutputMetadataRepository, archive_storage: ILargeFileStorage
    ) -> None:
        self._archive_storage = archive_storage
        self._metadata_repository = metadata_repository
        self._tmp_dir = tmp_dir

    def _get_metadata(self, study_id: str, output_name: str) -> OutputMetadata | None:
        return self._metadata_repository.get(study_id, output_name)

    def _require_metadata(self, study_id: str, output_name: str) -> OutputMetadata:
        metadata = self._metadata_repository.get(study_id, output_name)
        if metadata is None:
            raise OutputNotFound(f"Output {output_name} does not exist.")
        return metadata

    @override
    @property
    def storage_type(self) -> OutputStorageType:
        return OutputStorageType.V2

    @override
    def import_output(
        self, study_id: str, output: BinaryIO | Path, output_name_suffix: Optional[str] = None
    ) -> Optional[str]:
        logger.info(f"Importing output for study {study_id} to internal storage.")
        timer = StopWatch()
        tmp_dir = self._tmp_dir / f"output-import-{study_id}-{uuid.uuid4()}"
        tmp_dir.mkdir(parents=True)
        try:
            # We first ensure we have 2 versions of the output: compressed and uncompressed
            archive_path, dir_path = _write_temporary_files(tmp_dir, output)
            output_name = extract_output_name(dir_path, output_name_suffix)

            # Write the compressed version to archive storage
            self._archive_storage.write_file(_archive_id(study_id, output_name), archive_path)

            # Create metadata
            metadata = extract_metadata(dir_path)

            # TODO here: extract variables values

            self._metadata_repository.save(
                OutputMetadata(
                    study_id=study_id,
                    output_name=output_name,
                    archived=False,
                    type=metadata.type,
                )
            )
            timer.log_elapsed(lambda duration: logger.info(f"Output imported to internal storage in {duration}s."))
            return output_name
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @override
    def get_study_sim_result(self, study_id: str) -> List[StudySimResultDTO]:
        outputs = self._metadata_repository.get_all(study_id)
        return [_metadata_to_sim_result(m) for m in outputs]

    @override
    def list_outputs(self, study_id: str) -> list[BasicOutputMetadata]:
        return [
            BasicOutputMetadata(id=o.output_name, in_study=False) for o in self._metadata_repository.get_all(study_id)
        ]

    @override
    def get_simulations(self, study_id: str) -> dict[str, Simulation]:
        # TODO
        return {}

    @override
    def copy_output(self, src_study_id: str, target_study_id: str, output_id: str) -> None:
        # TODO
        pass

    @override
    def delete_output(self, study_id: str, output_id: str) -> None:
        # TODO: we should have some sort of synchronization so that
        #       the output appears deleted asap.
        #       Maybe only mark it deleted, and have it removed in the background.
        logger.info(f"Deleting output {study_id}/{output_id} from internal storage.")
        self._require_metadata(study_id, output_id)
        self._archive_storage.delete_file(_archive_id(study_id, output_id))
        self._metadata_repository.delete(study_id, output_id)

    @override
    def export_output(self, study_id: str, output_id: str, target: Path) -> None:
        logger.info(f"Exporting output {study_id}/{output_id} from internal storage.")
        self._require_metadata(study_id, output_id)
        self._archive_storage.read_file(_archive_id(study_id, output_id), target)

    @override
    def output_exists(self, study_id: str, output_id: str) -> bool:
        return self._get_metadata(study_id, output_id) is not None

    @override
    def is_output_archived(self, study_id: str, output_id: str) -> bool:
        metadata = self._require_metadata(study_id, output_id)
        return metadata.archived

    @override
    def archive_study_output(self, study_id: str, output_id: str) -> None:
        # For now, only a logical operation
        logger.info(f"Archiving output {study_id}/{output_id} in internal storage.")
        metadata = self._require_metadata(study_id, output_id)
        metadata.archived = True
        self._metadata_repository.save(metadata)

    @override
    def unarchive_study_output(self, study_id: str, output_id: str) -> None:
        # For now, only a logical operation
        logger.info(f"Unarchiving output {study_id}/{output_id} in internal storage.")
        metadata = self._require_metadata(study_id, output_id)
        metadata.archived = False
        self._metadata_repository.save(metadata)

    @override
    def get_digest(self, study_id: str, output_id: str) -> DigestUI:
        raise NotImplementedError()

    @override
    def get_output_time_index(self, study_id: str, output_id: str, frequency: MatrixFrequency) -> MatrixIndex:
        raise NotImplementedError()

    @override
    def aggregate_output_data(
        self,
        study_id: str,
        output_id: str,
        query_file: QueryFileType,
        frequency: MatrixFrequency,
        ids_to_consider: Sequence[str],
        columns_names: Sequence[str],
        transform_columns_headers: bool,
        mc_years: Optional[Sequence[int]] = None,
    ) -> Iterator[pd.DataFrame]:
        raise NotImplementedError()

    @override
    def extract_variables_list(self, study_id: str, output_id: str) -> OutputVariablesList:
        raise NotImplementedError()

    @override
    def write_output_to_dir(self, study_id: str, output_id: str, parent: Path) -> None:
        pass  # TODO
