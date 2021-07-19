import logging
import time
from pathlib import Path
from typing import Tuple

from antarest.matrixstore.service import MatrixService
from antarest.storage.business.uri_resolver_service import UriResolverService
from antarest.storage.repository.filesystem.config.files import (
    ConfigPathBuilder,
)
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.root.filestudytree import FileStudyTree

logger = logging.getLogger(__name__)


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
    ) -> Tuple[StudyConfig, FileStudyTree]:
        start_time = time.time()
        config = ConfigPathBuilder.build(path, study_id)
        duration = "{:.3f}".format(time.time() - start_time)
        logger.info(f"Study {study_id} config built in {duration}s")
        return config, FileStudyTree(self.context, config)

    def create_from_config(self, config: StudyConfig) -> FileStudyTree:
        return FileStudyTree(self.context, config)
