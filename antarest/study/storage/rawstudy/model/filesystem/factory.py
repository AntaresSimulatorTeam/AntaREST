import logging
import time
from pathlib import Path
from typing import Tuple

from dataclasses import dataclass

from antarest.core.interfaces.cache import ICache
from antarest.matrixstore.service import MatrixService
from antarest.study.common.uri_resolver_service import (
    UriResolverService,
)
from antarest.study.storage.rawstudy.model.filesystem.config.files import (
    ConfigPathBuilder,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)

logger = logging.getLogger(__name__)


@dataclass
class FileStudy:
    config: FileStudyTreeConfig
    tree: FileStudyTree


class StudyFactory:
    """
    Study Factory. Mainly used in test to inject study mock by dependency injection.
    """

    def __init__(
        self,
        matrix: MatrixService,
        resolver: UriResolverService,
        cache: ICache,
    ) -> None:
        self.context = ContextServer(matrix=matrix, resolver=resolver)
        self.cache = cache

    def create_from_fs(
        self, path: Path, study_id: str
    ) -> Tuple[FileStudyTreeConfig, FileStudyTree]:
        cache_id = f"{str(path)}/STUDY_FACTORY"
        from_cache = self.cache.get(cache_id)
        if from_cache:
            logger.info(f"Study {study_id} read from cache")
            return from_cache.data

        start_time = time.time()
        config = ConfigPathBuilder.build(path, study_id)
        duration = "{:.3f}".format(time.time() - start_time)
        logger.info(f"Study {study_id} config built in {duration}s")
        to_cache = config, FileStudyTree(self.context, config)
        self.cache.put(cache_id, to_cache)
        logger.info(f"Cache new entry from StudyFactory (studyID: {study_id})")
        return to_cache

    def create_from_config(self, config: FileStudyTreeConfig) -> FileStudyTree:
        return FileStudyTree(self.context, config)
