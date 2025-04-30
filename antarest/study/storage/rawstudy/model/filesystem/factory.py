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
import os.path
import tempfile
import time
from pathlib import Path
from typing import NamedTuple, Optional

import filelock
from antares.study.version import StudyVersion

from antarest.core.interfaces.cache import ICache, study_config_cache_key
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.storage.rawstudy.model.filesystem.config.files import build, parse_outputs
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    FileStudyTreeConfigDTO,
    validate_config,
)
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree

logger = logging.getLogger(__name__)


class FileStudy(NamedTuple):
    """
    Antares study stored on the disk.

    Attributes:
        config: Root object to handle all study parameters which impact tree structure.
        tree: Top level node of antares tree structure.
    """

    config: FileStudyTreeConfig
    tree: FileStudyTree


class StudyFactory:
    """
    Study Factory. Mainly used in test to inject study mock by dependency injection.
    """

    def __init__(
        self,
        matrix: ISimpleMatrixService,
        resolver: UriResolverService,
        cache: ICache,
    ) -> None:
        self.context = ContextServer(matrix=matrix, resolver=resolver)
        self.cache = cache
        # It is better to store lock files in the temporary directory,
        # because it is possible that there not deleted when the web application is stopped.
        # Cleaning up lock files is thus easier.
        self._lock_dir = tempfile.gettempdir()
        self._lock_fmt = "{basename}.create_from_fs.lock"

    def create_from_fs(
        self,
        path: Path,
        study_id: str,
        output_path: Optional[Path] = None,
        use_cache: bool = True,
    ) -> FileStudy:
        """
        Create a study from a path on the disk.

        `FileStudy` creation is done with a file lock to avoid that two studies are analyzed at the same time.

        Args:
            path: full path of the study directory to parse.
            study_id: ID of the study (if known).
            output_path: full path of the "output" directory in the study directory.
            use_cache: Whether to use cache or not.

        Returns:
            Antares study stored on the disk.
        """
        # This file lock is used to avoid that two studies are analyzed at the same time.
        # This often happens when the user opens a study, because we display both
        # the summary and the comments in the same time in the UI.
        lock_basename = study_id if study_id else path.name
        lock_file = os.path.join(self._lock_dir, self._lock_fmt.format(basename=lock_basename))
        with filelock.FileLock(lock_file):
            logger.info(f"🏗 Creating a study by reading the configuration from the directory '{path}'...")
            return self._create_from_fs_unsafe(path, study_id, output_path, use_cache)

    def _create_from_fs_unsafe(
        self,
        path: Path,
        study_id: str,
        output_path: Optional[Path] = None,
        use_cache: bool = True,
    ) -> FileStudy:
        cache_id = study_config_cache_key(study_id)
        if study_id and use_cache:
            from_cache = self.cache.get(cache_id)
            if from_cache is not None:
                logger.info(f"Study {study_id} read from cache")
                version = StudyVersion.parse(from_cache["version"])
                config = validate_config(version, from_cache)
                if output_path:
                    config.output_path = output_path
                    config.outputs = parse_outputs(output_path)
                return FileStudy(config, FileStudyTree(self.context, config))
        start_time = time.time()
        config = build(path, study_id, output_path)
        duration = "{:.3f}".format(time.time() - start_time)
        logger.info(f"Study {study_id} config built in {duration}s")
        result = FileStudy(config, FileStudyTree(self.context, config))
        if study_id and use_cache:
            logger.info(f"Cache new entry from StudyFactory (studyID: {study_id})")
            self.cache.put(
                cache_id,
                FileStudyTreeConfigDTO.from_build_config(config).model_dump(),
            )
        return result

    def create_from_config(self, config: FileStudyTreeConfig) -> FileStudyTree:
        return FileStudyTree(self.context, config)
