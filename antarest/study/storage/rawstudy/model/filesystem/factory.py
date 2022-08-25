import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from antarest.core.interfaces.cache import ICache, CacheConstants
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.matrixstore.uri_resolver_service import (
    UriResolverService,
)
from antarest.study.storage.rawstudy.model.filesystem.config.files import (
    ConfigPathBuilder,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    FileStudyTreeConfigDTO,
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
        matrix: ISimpleMatrixService,
        resolver: UriResolverService,
        cache: ICache,
    ) -> None:
        self.context = ContextServer(matrix=matrix, resolver=resolver)
        self.cache = cache

    def create_from_fs(
        self,
        path: Path,
        study_id: str,
        output_path: Optional[Path] = None,
        use_cache: bool = True,
    ) -> FileStudy:
        cache_id = f"{CacheConstants.STUDY_FACTORY}/{study_id}"
        if study_id and use_cache:
            from_cache = self.cache.get(cache_id)
            if from_cache is not None:
                logger.info(f"Study {study_id} read from cache")
                config = FileStudyTreeConfigDTO.parse_obj(
                    from_cache
                ).to_build_config()
                return FileStudy(config, FileStudyTree(self.context, config))
        start_time = time.time()
        config = ConfigPathBuilder.build(path, study_id, output_path)
        duration = "{:.3f}".format(time.time() - start_time)
        logger.info(f"Study {study_id} config built in {duration}s")
        result = FileStudy(config, FileStudyTree(self.context, config))
        if study_id and use_cache:
            self.cache.put(
                cache_id,
                FileStudyTreeConfigDTO.from_build_config(config).dict(),
            )
        logger.info(f"Cache new entry from StudyFactory (studyID: {study_id})")
        return result

    def create_from_config(self, config: FileStudyTreeConfig) -> FileStudyTree:
        return FileStudyTree(self.context, config)
