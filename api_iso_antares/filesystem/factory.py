from pathlib import Path
from typing import Tuple

from api_iso_antares.custom_types import JSON
from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.root.study import Study


class StudyFactory:
    def create_from_fs(self, path: Path) -> Tuple[Config, Study]:
        config = Config.from_path(path)
        return config, Study(config)

    def create_from_config(self, config: Config) -> Study:
        return Study(config)

    def create_from_json(self, path: Path, json: JSON) -> Tuple[Config, Study]:
        config = Config.from_json(json, path)
        return config, Study(config)
