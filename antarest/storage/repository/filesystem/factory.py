from pathlib import Path
from typing import Tuple

from antarest.common.custom_types import JSON
from antarest.matrixstore.service import MatrixService
from antarest.storage.repository.filesystem.config.files import (
    ConfigPathBuilder,
)
from antarest.storage.repository.filesystem.config.json import (
    ConfigJsonBuilder,
)
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.root.study import Study


class StudyFactory:
    """
    Study Factory. Mainly used in test to inject study mock by dependency injection.
    """

    def __init__(self, matrix: MatrixService) -> None:
        self.context = ContextServer(matrix=matrix)

    def create_from_fs(
        self, path: Path, study_id: str
    ) -> Tuple[StudyConfig, Study]:
        config = ConfigPathBuilder.build(path, study_id)
        return config, Study(self.context, config)

    def create_from_config(self, config: StudyConfig) -> Study:
        return Study(self.context, config)

    def create_from_json(
        self, path: Path, json: JSON, study_id: str
    ) -> Tuple[StudyConfig, Study]:
        config = ConfigJsonBuilder.build(path, json, study_id)
        return config, Study(self.context, config)
