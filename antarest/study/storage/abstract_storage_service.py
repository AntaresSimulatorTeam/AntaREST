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
import tempfile
from abc import ABC
from pathlib import Path
from typing import BinaryIO, List, Optional
from uuid import uuid4

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.exceptions import BadOutputError, StudyOutputNotFoundError
from antarest.core.interfaces.cache import ICache, study_raw_cache_key
from antarest.core.model import JSON, PublicMode
from antarest.core.serde.json import from_json
from antarest.core.utils.archives import ArchiveFormat, archive_dir, extract_archive, unzip
from antarest.core.utils.utils import StopWatch
from antarest.login.model import GroupDTO
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    OwnerInfo,
    Patch,
    PatchStudy,
    Study,
    StudyAdditionalData,
    StudyMetadataDTO,
    StudySimResultDTO,
    StudySimSettingsDTO,
)
from antarest.study.storage.output_storage import IOutputStorage
from antarest.study.storage.rawstudy.model.filesystem.config.files import get_playlist
from antarest.study.storage.rawstudy.model.filesystem.config.model import Simulation
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.rawstudy.model.filesystem.inode import OriginalFile
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers
from antarest.study.storage.study_storage import IStudyStorage
from antarest.study.storage.utils import extract_output_name, fix_study_root, remove_from_cache

logger = logging.getLogger(__name__)


class AbstractStorageService(IStudyStorage, IOutputStorage, ABC):
    def __init__(
        self,
        config: Config,
        study_factory: StudyFactory,
        cache: ICache,
    ):
        self.config: Config = config
        self.study_factory: StudyFactory = study_factory
        self.cache = cache

    @override
    def get_study_information(
        self,
        study: Study,
    ) -> StudyMetadataDTO:
        additional_data = study.additional_data or StudyAdditionalData()

        try:
            patch_str = additional_data.patch or "{}"
            patch = Patch.model_validate(from_json(patch_str))
        except ValueError as e:
            # The conversion to JSON and the parsing can fail if the patch is not valid
            logger.warning(f"Failed to parse patch for study {study.id}", exc_info=e)
            patch = Patch()

        patch_metadata = patch.study or PatchStudy()

        study_workspace = getattr(study, "workspace", DEFAULT_WORKSPACE_NAME)
        folder: Optional[str] = None
        if hasattr(study, "folder"):
            folder = study.folder

        owner_info = (
            OwnerInfo(id=study.owner.id, name=study.owner.name)
            if study.owner is not None
            else OwnerInfo(name=additional_data.author or "Unknown")
        )

        return StudyMetadataDTO(
            id=study.id,
            name=study.name,
            version=study.version,
            created=str(study.created_at),
            updated=str(study.updated_at),
            workspace=study_workspace,
            managed=study_workspace == DEFAULT_WORKSPACE_NAME,
            type=study.type,
            archived=study.archived if study.archived is not None else False,
            owner=owner_info,
            groups=[GroupDTO(id=group.id, name=group.name) for group in study.groups],
            public_mode=study.public_mode or PublicMode.NONE,
            horizon=additional_data.horizon,
            scenario=patch_metadata.scenario,
            status=patch_metadata.status,
            doc=patch_metadata.doc,
            folder=folder,
            tags=[tag.label for tag in study.tags],
        )

    @override
    def get(
        self,
        metadata: Study,
        url: str = "",
        depth: int = 3,
        formatted: bool = True,
        use_cache: bool = True,
    ) -> JSON:
        """
        Entry point to fetch data inside study.
        Args:
            metadata: study
            url: path data inside study to reach
            depth: tree depth to reach after reach data path
            formatted: indicate if raw files must be parsed and formatted
            use_cache: indicate if the cache must be used

        Returns: study data formatted in json

        """
        self._check_study_exists(metadata)
        study = self.get_raw(metadata, use_cache)
        parts = [item for item in url.split("/") if item]

        if url == "" and depth == -1:
            cache_id = study_raw_cache_key(metadata.id)
            from_cache: Optional[JSON] = None
            if use_cache:
                from_cache = self.cache.get(cache_id)
            if from_cache is not None:
                logger.info(f"Raw Study {metadata.id} read from cache")
                data = from_cache
            else:
                data = study.tree.get(parts, depth=depth, formatted=formatted)
                self.cache.put(cache_id, data)
                logger.info(f"Cache new entry from RawStudyService (studyID: {metadata.id})")
        else:
            data = study.tree.get(parts, depth=depth, formatted=formatted)
        del study
        return data

    @override
    def get_file(
        self,
        metadata: Study,
        url: str = "",
        use_cache: bool = True,
    ) -> OriginalFile:
        """
        Entry point to fetch data inside study.
        Args:
            metadata: study
            url: path data inside study to reach
            use_cache: indicate if the cache must be used

        Returns: a file content with its extension and name

        """
        self._check_study_exists(metadata)
        study = self.get_raw(metadata, use_cache)
        parts = [item for item in url.split("/") if item]

        file_node = study.tree.get_node(parts)

        return file_node.get_file_content()

    @override
    def get_study_sim_result(
        self,
        study: Study,
    ) -> List[StudySimResultDTO]:
        """
        Get global result information
        Args:
            study: study
        Returns: study output data
        """
        study_data = self.get_raw(study)
        results: List[StudySimResultDTO] = []
        if study_data.config.outputs is not None:
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
                        f"Failed to retrieve info about output {output} in study {study.name} ({study.id}",
                        exc_info=e,
                    )
        return results

    @override
    def import_output(
        self,
        metadata: Study,
        output: BinaryIO | Path,
        output_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Import additional output in an existing study.

        Args:
            metadata: study
            output: new output (path or zipped data)
            output_name: optional suffix name to append to output name

        Returns:
            Output identifier.

        Raises:
            BadArchiveContent: If the output archive is corrupted or in an unknown format.
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
    def export_study(self, metadata: Study, target: Path, outputs: bool = True) -> Path:
        """
        Export and compress the study inside a 7zip file.

        Args:
            metadata: Study metadata object.
            target: Path of the file to export to.
            outputs: Flag to indicate whether to include the output folder inside the exportation.

        Returns:
            The 7zip file containing the study files compressed inside.
        """
        path_study = Path(metadata.path)
        with tempfile.TemporaryDirectory(dir=self.config.storage.tmp_dir) as tmpdir:
            logger.info(f"Exporting study {metadata.id} to temporary path {tmpdir}")
            tmp_study_path = Path(tmpdir) / "tmp_copy"
            self.export_study_flat(metadata, tmp_study_path, outputs)
            stopwatch = StopWatch()
            archive_dir(tmp_study_path, target)
            stopwatch.log_elapsed(
                lambda x: logger.info(f"Study {path_study} exported ({target.suffix} format) in {x}s")
            )
        return target

    @override
    def export_output(self, metadata: Study, output_id: str, target: Path) -> None:
        """
        Export and compresses study inside zip
        Args:
            metadata: study
            output_id: output id
            target: path of the file to export to
        """
        logger.info(f"Exporting output {output_id} from study {metadata.id}")

        path_output = Path(metadata.path) / "output" / output_id
        path_output_zip = Path(metadata.path) / "output" / f"{output_id}{ArchiveFormat.ZIP}"

        if path_output_zip.exists():
            shutil.copyfile(path_output_zip, target)
            return None

        if not path_output.exists() and not path_output_zip.exists():
            raise StudyOutputNotFoundError()
        stopwatch = StopWatch()
        if not path_output_zip.exists():
            archive_dir(path_output, target, archive_format=ArchiveFormat.ZIP)
        stopwatch.log_elapsed(lambda x: logger.info(f"Output {output_id} from study {metadata.path} exported in {x}s"))

    def _read_additional_data_from_files(self, file_study: FileStudy) -> StudyAdditionalData:
        logger.info(f"Reading additional data from files for study {file_study.config.study_id}")
        horizon = file_study.tree.get(url=["settings", "generaldata", "general", "horizon"])
        author = file_study.tree.get(url=["study", "antares", "author"])
        assert isinstance(author, str)
        assert isinstance(horizon, (str, int))
        study_additional_data = StudyAdditionalData(horizon=horizon, author=author)
        return study_additional_data

    @override
    def archive_study_output(self, study: Study, output_id: str) -> bool:
        try:
            archive_dir(
                Path(study.path) / "output" / output_id,
                Path(study.path) / "output" / f"{output_id}{ArchiveFormat.ZIP}",
                remove_source_dir=True,
                archive_format=ArchiveFormat.ZIP,
            )
            remove_from_cache(self.cache, study.id)
            return True
        except Exception as e:
            logger.warning(
                f"Failed to archive study {study.name} output {output_id}",
                exc_info=e,
            )
            return False

    @override
    def unarchive_study_output(self, study: Study, output_id: str, keep_src_zip: bool) -> bool:
        if not (Path(study.path) / "output" / f"{output_id}{ArchiveFormat.ZIP}").exists():
            logger.warning(
                f"Failed to archive study {study.name} output {output_id}. Maybe it's already unarchived",
            )
            return False
        try:
            unzip(
                Path(study.path) / "output" / output_id,
                Path(study.path) / "output" / f"{output_id}{ArchiveFormat.ZIP}",
                remove_source_zip=not keep_src_zip,
            )
            remove_from_cache(self.cache, study.id)
            return True
        except Exception as e:
            logger.warning(
                f"Failed to unarchive study {study.name} output {output_id}",
                exc_info=e,
            )
            return False
