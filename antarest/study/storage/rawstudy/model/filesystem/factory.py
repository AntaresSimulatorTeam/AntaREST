import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from antarest.core.interfaces.cache import ICache, CacheConstants
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
        self,
        path: Path,
        study_id: str,
        use_cache: bool = True,
    ) -> Tuple[FileStudyTreeConfig, FileStudyTree]:
        cache_id = f"{study_id}/{CacheConstants.STUDY_FACTORY}"
        if study_id and use_cache:
            from_cache = self.cache.get(cache_id)
            if from_cache is not None:
                logger.info(f"Study {study_id} read from cache")
                config = FileStudyTreeConfig.parse_obj(from_cache)
                return config, FileStudyTree(self.context, config)
        start_time = time.time()
        config = ConfigPathBuilder.build(path, study_id)
        duration = "{:.3f}".format(time.time() - start_time)
        logger.info(f"Study {study_id} config built in {duration}s")
        result = config, FileStudyTree(self.context, config)
        if study_id and use_cache:
            self.cache.put(cache_id, config.dict())
        logger.info(f"Cache new entry from StudyFactory (studyID: {study_id})")
        return result

    def create_from_config(self, config: FileStudyTreeConfig) -> FileStudyTree:
        return FileStudyTree(self.context, config)
