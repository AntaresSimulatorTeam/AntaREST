# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
import time
import typing as t
from datetime import datetime
from pathlib import Path
from threading import Thread
from uuid import uuid4
from zipfile import ZipFile

from antares.study.version import StudyVersion

from antarest.core.config import Config
from antarest.core.exceptions import StudyDeletionNotAllowed
from antarest.core.interfaces.cache import ICache
from antarest.core.model import PublicMode
from antarest.core.requests import RequestParameters
from antarest.core.utils.utils import extract_zip
from antarest.study.model import DEFAULT_WORKSPACE_NAME, Patch, RawStudy, Study, StudyAdditionalData
from antarest.study.storage.abstract_storage_service import AbstractStorageService
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig, FileStudyTreeConfigDTO
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode
from antarest.study.storage.utils import (
    create_new_empty_study,
    export_study_flat,
    fix_study_root,
    is_managed,
    remove_from_cache,
    update_antares_info,
)

logger = logging.getLogger(__name__)


class RawStudyService(AbstractStorageService[RawStudy]):
    """
    Manage set of raw studies stored in the workspaces.
    Instantiate and manage tree struct for each request

    """

    def __init__(
        self,
        config: Config,
        study_factory: StudyFactory,
        path_resources: Path,
        patch_service: PatchService,
        cache: ICache,
    ):
        super().__init__(
            config=config,
            study_factory=study_factory,
            patch_service=patch_service,
            cache=cache,
        )
        self.path_resources: Path = path_resources
        self.cleanup_thread = Thread(
            target=RawStudyService.cleanup_lazynode_zipfilelist_cache,
            name=f"{self.__class__.__name__}-Cleaner",
            daemon=True,
        )
        self.cleanup_thread.start()

    def update_from_raw_meta(self, metadata: RawStudy, fallback_on_default: t.Optional[bool] = False) -> None:
        """
        Update metadata from study raw metadata
        Args:
            metadata: study
            fallback_on_default: use default values in case of failure
        """
        path = self.get_study_path(metadata)
        study = self.study_factory.create_from_fs(path, study_id="")
        try:
            raw_meta = study.tree.get(["study", "antares"])
            metadata.name = raw_meta["caption"]
            metadata.version = raw_meta["version"]
            metadata.created_at = datetime.utcfromtimestamp(raw_meta["created"])
            metadata.updated_at = datetime.utcfromtimestamp(raw_meta["lastsave"])

            metadata.additional_data = self._read_additional_data_from_files(study)

        except Exception as e:
            logger.error(
                "Failed to fetch study %s raw metadata!",
                str(metadata.path),
                exc_info=e,
            )
            if fallback_on_default is not None:
                metadata.name = metadata.name or "unnamed"
                metadata.version = metadata.version or 0
                metadata.created_at = metadata.created_at or datetime.utcnow()
                metadata.updated_at = metadata.updated_at or datetime.utcnow()
                if metadata.additional_data is None:
                    metadata.additional_data = StudyAdditionalData()
                metadata.additional_data.patch = metadata.additional_data.patch or Patch().model_dump_json()
                metadata.additional_data.author = metadata.additional_data.author or "Unknown"

            else:
                raise e

    def update_name_and_version_from_raw_meta(self, metadata: RawStudy) -> bool:
        """
        Update name from study raw metadata
        Args:
            metadata: study
        Returns: a boolean indicating if the name or version has changed
        """
        path = self.get_study_path(metadata)
        try:
            study = self.study_factory.create_from_fs(path, study_id="")
            raw_meta = study.tree.get(["study", "antares"])
            version_as_string = str(raw_meta["version"])
            if metadata.name != raw_meta["caption"] or metadata.version != version_as_string:
                logger.info(
                    f"Updating name/version for study {metadata.id} ({metadata.name}) to {raw_meta['caption']}/{version_as_string}"
                )
                metadata.name = raw_meta["caption"]
                metadata.version = version_as_string
                return True
            return False
        except Exception as e:
            logger.error(
                "Failed to update study %s name and version from raw metadata!",
                str(metadata.path),
                exc_info=e,
            )
            return False

    def exists(self, study: RawStudy) -> bool:
        """
        Check study exist.
        Args:
            study: study

        Returns: true if study presents in disk, false else.

        """
        path = self.get_study_path(study)

        if study.archived:
            path = self.get_archive_path(study)
            zf = ZipFile(path, "r")
            return str("study.antares") in zf.namelist()

        return (path / "study.antares").is_file()

    def get_raw(
        self,
        metadata: RawStudy,
        use_cache: bool = True,
        output_dir: t.Optional[Path] = None,
    ) -> FileStudy:
        """
        Fetch a study object and its config
        Args:
            metadata: study
            use_cache: use cache
            output_dir: optional output dir override
        Returns: the config and study tree object

        """
        self._check_study_exists(metadata)
        study_path = self.get_study_path(metadata)
        return self.study_factory.create_from_fs(study_path, metadata.id, output_dir, use_cache=use_cache)

    def get_synthesis(self, metadata: RawStudy, params: t.Optional[RequestParameters] = None) -> FileStudyTreeConfigDTO:
        self._check_study_exists(metadata)
        study_path = self.get_study_path(metadata)
        study = self.study_factory.create_from_fs(study_path, metadata.id)
        return FileStudyTreeConfigDTO.from_build_config(study.config)

    def create(self, metadata: RawStudy) -> RawStudy:
        """
        Create a new empty study based on the given metadata.

        Args:
            metadata: An instance containing study information, eg.:

                - id: The study UUID.
                - name: The name of the study.
                - version: The version of the study template to be used.
                - path: The full path of the study directory in the "default" workspace.
                - author: The author's name (if provided) or "Unknown" if missing.
                - ...

        Returns:
            An updated `RawStudy` instance with the path to the newly created study.
        """
        path_study = Path(metadata.path)
        path_study.mkdir()

        create_new_empty_study(
            version=metadata.version,
            path_study=path_study,
            path_resources=self.path_resources,
        )

        study = self.study_factory.create_from_fs(path_study, metadata.id)
        update_antares_info(metadata, study.tree, update_author=True)

        metadata.path = str(path_study)

        return metadata

    def copy(
        self,
        src_meta: RawStudy,
        dest_name: str,
        groups: t.Sequence[str],
        with_outputs: bool = False,
    ) -> RawStudy:
        """
        Create a new RAW study by copying a reference study.

        Args:
            src_meta: The source study that you want to copy.
            dest_name: The name for the destination study.
            groups: A list of groups to assign to the destination study.
            with_outputs: Indicates whether to copy the outputs as well.

        Returns:
            The newly created study.
        """
        self._check_study_exists(src_meta)

        if src_meta.additional_data is None:
            additional_data = StudyAdditionalData()
        else:
            additional_data = StudyAdditionalData(
                horizon=src_meta.additional_data.horizon,
                author=src_meta.additional_data.author,
                patch=src_meta.additional_data.patch,
            )
        dest_id = str(uuid4())
        dest_study = RawStudy(
            id=dest_id,
            name=dest_name,
            workspace=DEFAULT_WORKSPACE_NAME,
            path=str(self.config.get_workspace_path() / dest_id),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=src_meta.version,
            additional_data=additional_data,
            public_mode=PublicMode.NONE if groups else PublicMode.READ,
            groups=groups,
        )

        src_path = self.get_study_path(src_meta)
        dest_path = self.get_study_path(dest_study)

        shutil.copytree(src_path, dest_path)

        output = dest_path / "output"
        if not with_outputs and output.exists():
            shutil.rmtree(output)

        study = self.study_factory.create_from_fs(dest_path, study_id=dest_study.id)
        update_antares_info(dest_study, study.tree, update_author=False)

        return dest_study

    def delete(self, metadata: RawStudy) -> None:
        """
        Delete study
        Args:
            metadata: study

        Returns:

        """
        self._check_study_exists(metadata)
        if self.config.storage.allow_deletion or is_managed(metadata):
            study_path = self.get_study_path(metadata)
            shutil.rmtree(study_path, ignore_errors=True)
            remove_from_cache(self.cache, metadata.id)
        else:
            raise StudyDeletionNotAllowed(metadata.id)

    def delete_output(self, metadata: RawStudy, output_name: str) -> None:
        """
        Delete output folder
        Args:
            metadata: study
            output_name: output simulation

        Returns:

        """
        study_path = self.get_study_path(metadata)
        output_path = study_path / "output" / output_name
        if output_path.exists() and output_path.is_dir():
            shutil.rmtree(output_path, ignore_errors=True)
        else:
            output_path = output_path.parent / f"{output_name}.zip"
            output_path.unlink(missing_ok=True)
        remove_from_cache(self.cache, metadata.id)

    def import_study(self, metadata: RawStudy, stream: t.BinaryIO) -> Study:
        """
        Import study in the directory of the study.

        Args:
            metadata: study information.
            stream: binary content of the study compressed in ZIP or 7z format.

        Returns:
            Updated study information.

        Raises:
            BadArchiveContent: If the archive is corrupted or in an unknown format.
        """
        path_study = Path(metadata.path)
        path_study.mkdir()

        try:
            extract_zip(stream, path_study)
            fix_study_root(path_study)
            self.update_from_raw_meta(metadata)

        except Exception:
            shutil.rmtree(path_study)
            raise

        metadata.path = str(path_study)
        return metadata

    def export_study_flat(
        self,
        metadata: RawStudy,
        dst_path: Path,
        outputs: bool = True,
        output_list_filter: t.Optional[t.List[str]] = None,
        denormalize: bool = True,
    ) -> None:
        try:
            if metadata.archived:
                self.unarchive(metadata)  # may raise BadArchiveContent

            export_study_flat(
                Path(metadata.path),
                dst_path,
                self.study_factory,
                outputs,
                output_list_filter,
                denormalize,
            )

        finally:
            if metadata.archived:
                shutil.rmtree(metadata.path, ignore_errors=True)

    def check_errors(
        self,
        metadata: RawStudy,
    ) -> t.List[str]:
        """
        Check study antares data integrity
        Args:
            metadata: study

        Returns: list of non integrity inside study

        """
        path = self.get_study_path(metadata)
        study = self.study_factory.create_from_fs(path, metadata.id)
        return study.tree.check_errors(study.tree.get())

    def set_reference_output(self, study: RawStudy, output_id: str, status: bool) -> None:
        self.patch_service.set_reference_output(study, output_id, status)
        remove_from_cache(self.cache, study.id)

    def archive(self, study: RawStudy) -> Path:
        archive_path = self.get_archive_path(study)
        new_study_path = self.export_study(study, archive_path)
        shutil.rmtree(study.path)
        remove_from_cache(cache=self.cache, root_id=study.id)
        self.cache.invalidate(study.id)
        return new_study_path

    # noinspection SpellCheckingInspection
    def unarchive(self, study: RawStudy) -> None:
        """
        Extract the archive of a study.

        Args:
            study: The study to be unarchived.

        Raises:
            BadArchiveContent: If the archive is corrupted or in an unknown format.
        """
        with open(self.get_archive_path(study), mode="rb") as fh:
            self.import_study(study, fh)

    def get_archive_path(self, study: RawStudy) -> Path:
        return Path(self.config.storage.archive_dir / f"{study.id}.zip")

    def get_study_path(self, metadata: Study) -> Path:
        """
        Get study path
        Args:
            metadata: study information

        Returns: study path

        """
        if metadata.archived:
            return self.get_archive_path(metadata)
        return Path(metadata.path)

    def initialize_additional_data(self, raw_study: RawStudy) -> bool:
        try:
            study = self.study_factory.create_from_fs(
                self.get_study_path(raw_study),
                study_id=raw_study.id,
            )
            raw_study.additional_data = self._read_additional_data_from_files(study)
            return True
        except Exception as e:
            logger.error(
                f"Error while reading additional data for study {raw_study.id}",
                exc_info=e,
            )
            return False

    def check_and_update_study_version_in_database(self, study: RawStudy) -> None:
        try:
            study_path = self.get_study_path(study)
            if study_path:
                config = FileStudyTreeConfig(
                    study_path=study_path,
                    path=study_path,
                    study_id="",
                    version=StudyVersion.parse(-1),
                )
                raw_study = self.study_factory.create_from_config(config)
                file_metadata = raw_study.get(url=["study", "antares"])
                study_version = str(file_metadata.get("version", study.version))
                if study_version != study.version:
                    logger.warning(
                        f"Study version in file ({study_version}) is different from the one stored in db ({study.version}), returning file version"
                    )
                    study.version = study_version
        except Exception as e:
            logger.error(
                "Failed to check and/or update study version in database for study %s",
                study.id,
                exc_info=e,
            )

    @staticmethod
    def cleanup_lazynode_zipfilelist_cache() -> None:
        while True:
            logger.info(f"Cleaning lazy node zipfilelist cache ({len(LazyNode.ZIP_FILELIST_CACHE)} items)")
            LazyNode.ZIP_FILELIST_CACHE = {
                key: LazyNode.ZIP_FILELIST_CACHE[key]
                for key in LazyNode.ZIP_FILELIST_CACHE
                if LazyNode.ZIP_FILELIST_CACHE[key].expiration_date < datetime.utcnow()
            }
            logger.info(f"Cleaned lazy node zipfilelist cache ({len(LazyNode.ZIP_FILELIST_CACHE)} items)")
            time.sleep(600)
