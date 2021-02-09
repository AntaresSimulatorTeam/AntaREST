from pathlib import Path
from typing import Tuple

from antarest.common.custom_types import JSON
from antarest.storage.repository.filesystem.config.files import (
    ConfigPathBuilder,
)
from antarest.storage.repository.filesystem.config.json import (
    ConfigJsonBuilder,
)
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.root.study import Study


class StudyFactory:
    def create_from_fs(self, path: Path) -> Tuple[StudyConfig, Study]:
        config = ConfigPathBuilder.build(path)
        return config, Study(config)

    def create_from_config(self, config: StudyConfig) -> Study:
        return Study(config)

    def create_from_json(
        self, path: Path, json: JSON
    ) -> Tuple[StudyConfig, Study]:
        config = ConfigJsonBuilder.build(path, json)
        return config, Study(config)
