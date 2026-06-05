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
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Iterator

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.utils.utils import current_time
from antarest.matrixstore.model import MatrixReference
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.model import RawStudy, Study
from antarest.study.storage.file_study_utils import export_study_to_flat_directory, get_study_path, update_antares_info
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
    extract_matrix_id,
)
from antarest.study.storage.study_storage_interface import IStudyStorage
from antarest.study.storage.utils import extract_data_to_dir, get_disk_usage, is_managed

logger = logging.getLogger(__name__)


class FileStudyStorage(IStudyStorage):
    def __init__(self, config: Config, matrix_service: ISimpleMatrixService, study_factory: StudyFactory):
        self._config = config
        self._study_factory = study_factory
        self._matrix_service = matrix_service

    @override
    def copy(self, src_study: Study, new_study: RawStudy) -> RawStudy:
        src_path = get_study_path(src_study)
        dest_path = Path(new_study.path)

        shutil.copytree(src_path, dest_path, ignore=shutil.ignore_patterns("output"))

        file_study = self._get_file_study(dest_path, True, new_study.id)

        update_antares_info(new_study, file_study.tree, update_author=False)

        self.normalize_file_study(file_study)

        return new_study

    @override
    def write_study_for_archive(self, study: RawStudy, dst_path: Path) -> None:
        shutil.copytree(src=Path(study.path), dst=dst_path)
        file_study = self._get_file_study(dst_path, False)
        self._denormalize_file_study(file_study)

    @override
    def export_study(self, study: Study, dst_path: Path) -> None:
        export_study_to_flat_directory(get_study_path(study), dst_path)
        file_study = self._get_file_study(dst_path, False)
        self._denormalize_file_study(file_study)

    @override
    def yield_matrix_references(self, study: Study) -> Iterator[MatrixReference]:
        study_path = get_study_path(study)
        study_id = study.id
        if study_path.exists():
            description: str
            if isinstance(study, RawStudy):
                description = f"Used by raw study {study_id}"
            else:
                description = f"Used by variant study {study_id} snapshot"

            # Only check `input` and `user/expansion` path as they are the only folders capable of having `.link` files.
            for path in [study_path / "input", study_path / "user" / "expansion"]:
                for f in path.rglob("*.link"):
                    matrix_id = extract_matrix_id(f.read_text())
                    matrix_reference = MatrixReference(matrix_id=matrix_id, use_description=description)
                    yield matrix_reference

    @override
    def get_disk_usage(self, study: Study) -> int:
        # We need to exclude the output folder
        study_path = Path(study.path)

        if not study_path.exists():
            # Could be the case for a variant that was not generated yet
            return 0

        total_disk_usage = 0
        for entry in study_path.iterdir():
            if entry.name != "output":
                total_disk_usage += get_disk_usage(entry)
        return total_disk_usage

    @override
    def normalize_study(self, study: Study) -> None:
        file_study = self._get_file_study(Path(study.path), is_managed(study), study.id)
        self.normalize_file_study(file_study)

    def normalize_file_study(self, file_study: FileStudy) -> None:
        matrix_nodes = file_study.tree.get_matrix_nodes_to_normalize()
        if not matrix_nodes:
            return

        matrix_ids = self._matrix_service.create_batch(node.parse_content() for node in matrix_nodes)
        for k, node in enumerate(matrix_nodes):
            node.save_matrix(matrix_ids[k])

    @override
    def import_study(self, study: RawStudy, stream: BinaryIO) -> None:
        extract_data_to_dir(Path(study.path), stream, self._config.storage.tmp_dir)
        self.update_from_raw_metadata(study)
        self.normalize_study(study)

    def update_from_raw_metadata(self, study: Study) -> None:
        """
        The given `study` object needs to be updated according to the real filesystem data
        """
        file_study = self._get_file_study(Path(study.path), is_managed(study))
        try:
            raw_meta = file_study.tree.get(["study", "antares"])

            if study.editor:
                raw_meta["editor"] = study.editor
                file_study.tree.save(raw_meta, ["study", "antares"])

            study.name = raw_meta["caption"]
            study.version = str(raw_meta["version"])
            study.created_at = datetime.utcfromtimestamp(raw_meta["created"])
            study.updated_at = datetime.utcfromtimestamp(raw_meta["lastsave"])

            self._update_study_data_from_files(file_study, study)

        except Exception as e:
            logger.error("Failed to fetch study %s raw study!", str(study.path), exc_info=e)
            study.name = study.name or "unnamed"
            study.created_at = study.created_at or current_time()
            study.updated_at = study.updated_at or current_time()
            study.author = study.author or "Unknown"
            study.editor = study.editor or "Unknown"

    def update_name_and_version_from_raw_meta(self, study: RawStudy) -> bool:
        path = Path(study.path)
        try:
            file_study = self._get_file_study(path, is_managed(study))
            raw_meta = file_study.tree.get(["study", "antares"])
            version_as_string = str(raw_meta["version"])
            if study.name != raw_meta["caption"] or study.version != version_as_string:
                logger.info(
                    f"Updating name/version for study {study.id} ({study.name}) to {raw_meta['caption']}/{version_as_string}"
                )
                study.name = raw_meta["caption"]
                study.version = version_as_string
                return True
            return False
        except Exception as e:
            logger.error("Failed to update study %s name and version from raw metadata!", str(study.path), exc_info=e)
            return False

    def _update_study_data_from_files(self, file_study: FileStudy, study: Study) -> None:
        logger.info(f"Reading additional data from files for study {file_study.config.study_id}")
        horizon = file_study.tree.get(url=["settings", "generaldata", "general", "horizon"])
        study_antares = file_study.tree.get(url=["study", "antares"])
        author = study_antares.get("author")
        editor = study_antares.get("editor", author)
        assert isinstance(author, str)
        assert isinstance(editor, str)
        assert isinstance(horizon, (str, int))
        study.horizon = horizon
        study.author = author
        study.editor = editor

    def _get_file_study(self, study_path: Path, managed: bool, study_id: str = "") -> FileStudy:
        return self._study_factory.create_from_fs(study_path, managed, study_id=study_id)

    def denormalize_study(self, study: Study) -> None:
        file_study = self._get_file_study(Path(study.path), is_managed(study), study.id)
        self._denormalize_file_study(file_study)

    def _denormalize_file_study(self, file_study: FileStudy) -> None:
        matrix_nodes = file_study.tree.get_matrix_nodes_to_denormalize()
        if not matrix_nodes:
            return

        matrices_mapping: dict[str, list[InputSeriesMatrix]] = {}
        for node in matrix_nodes:
            link_content = node.get_matrix_id()
            assert link_content is not None
            matrices_mapping.setdefault(link_content, []).append(node)

        for matrix_content in self._matrix_service.yield_matrices(list(matrices_mapping)):
            for node in matrices_mapping[matrix_content.id]:
                node.write_dataframe(matrix_content.data)
