import logging
import time
from pathlib import Path
from typing import Tuple

from dataclasses import dataclass

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
        self, matrix: MatrixService, resolver: UriResolverService
    ) -> None:
        self.context = ContextServer(matrix=matrix, resolver=resolver)

    def create_from_fs(
        self, path: Path, study_id: str
    ) -> Tuple[FileStudyTreeConfig, FileStudyTree]:
        start_time = time.time()
        config = ConfigPathBuilder.build(path, study_id)
        duration = "{:.3f}".format(time.time() - start_time)
        logger.info(f"Study {study_id} config built in {duration}s")
        return config, FileStudyTree(self.context, config)

    def create_from_config(self, config: FileStudyTreeConfig) -> FileStudyTree:
        return FileStudyTree(self.context, config)
