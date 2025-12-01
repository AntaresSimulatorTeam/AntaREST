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
from pathlib import Path
from typing import Iterator, Sequence

import pandas as pd

from antarest.core.exceptions import StudyOutputNotFoundError
from antarest.core.utils.archives import ArchiveFormat, archive_dir, unzip
from antarest.core.utils.utils import StopWatch
from antarest.study.business.output.aggregator_management import AggregatorManager
from antarest.study.business.output.utils import (
    MCAllAreasQueryFile,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import (
    DigestSynthesis,
    DigestUI,
)

logger = logging.getLogger(__name__)


class FileOutput:
    """
    Design notes: only sync methods
    """

    def __init__(self, study_id: str, file_study: FileStudy, output_name: str):
        self.study_id = study_id
        self.output_name = output_name
        self.file_study = file_study

    @property
    def _path(self) -> Path:
        # TODO: does this work for variants ?
        return self._get_study_path() / "output" / self.output_name

    @property
    def _archive_path(self) -> Path:
        return self._get_study_path() / "output" / f"{self.output_name}{ArchiveFormat.ZIP}"

    def _get_study_path(self) -> Path:
        return Path(self.file_study.config.study_path)

    def is_archived(self) -> bool:
        # Returns True it the given path is archived or if adding a suffix to the path points to an existing path
        archive_suffixes = [".zip"]
        suffix = self._path.suffixes[-1] if self._path.suffixes else None
        if suffix and suffix in archive_suffixes:
            return True
        return any((self._path.parent / (self._path.name + suffix)).exists() for suffix in archive_suffixes)

    def unarchive(self) -> bool:
        """
        Unarchives the output (synchronously)
        """
        if not self.is_archived():
            logger.warning(
                f"Failed to archive output {self.output_name}, it's already unarchived",
            )
            return False
        try:
            unzip(self._path, self._archive_path)
            # TODO: restore this elsewhere ? only to change the status of the output in the config cache I guess ?
            #       remove_from_cache(self.cache, study.id)
            # remove_from_cache(self.cache, study.id)
            return True
        except Exception as e:
            logger.warning(
                f"Failed to unarchive study {self.study_id} output {self.output_name}",
                exc_info=e,
            )
            return False

    def archive(self) -> bool:
        """
        Archives the output (synchronously)
        """
        try:
            archive_dir(
                self._path,
                self._get_study_path() / "output" / f"{self.output_name}{ArchiveFormat.ZIP}",
                remove_source_dir=True,
                archive_format=ArchiveFormat.ZIP,
            )
            # TODO: restore this elsewhere ? only to change the status of the output in the config cache I guess ?
            #       remove_from_cache(self.cache, study.id)
            return True
        except Exception as e:
            logger.warning(
                f"Failed to archive study {self.study_id} output {self.output_name}",
                exc_info=e,
            )
            return False

    # TODO: there is probably something better to use here than pandas dataframes
    def stream_aggregated_values(
        self,
        query_file: MCIndAreasQueryFile | MCAllAreasQueryFile | MCIndLinksQueryFile | MCAllLinksQueryFile,
        frequency: MatrixFrequency,
        columns_names: Sequence[str],
        ids_to_consider: Sequence[str],
        mc_years: Sequence[int] | None = None,
    ) -> Iterator[pd.DataFrame]:
        # TODO: Should just be a call, it makes no sense to have an object
        aggregator_manager = AggregatorManager(
            self._path,
            query_file,
            frequency,
            ids_to_consider,
            columns_names,
            mc_years,
        )
        return aggregator_manager.aggregate_output_data()

    def get_digest(self) -> DigestUI:
        digest_node = self.file_study.tree.get_node(
            url=["output", self.output_name, "economy", "mc-all", "grid", "digest"]
        )
        assert isinstance(digest_node, DigestSynthesis)
        return digest_node.get_ui()

    def export(self, export_path: Path) -> None:
        logger.info(f"Exporting output {self.output_name} from study {self.study_id} to {export_path}")

        path_output = self._path
        path_output_zip = self._archive_path

        if path_output_zip.exists():
            shutil.copyfile(path_output_zip, export_path)
            return None

        if not path_output.exists() and not path_output_zip.exists():
            raise StudyOutputNotFoundError()

        stopwatch = StopWatch()
        archive_dir(path_output, export_path, archive_format=ArchiveFormat.ZIP)
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Output {self.output_name} from study {self.study_id} exported in {x}s")
        )
