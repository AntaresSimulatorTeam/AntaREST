from typing import List

from api_iso_antares.custom_types import JSON, SUB_JSON
from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.inode import INode


class RawFileNode(INode):
    def __init__(self, config: Config):
        self.config = config

    def get(self, url: List[str]) -> SUB_JSON:
        if len(url) > 0:
            raise ValueError(
                f"url should be fully resolved when arrives on {self.__class__.__name__}"
            )
        return self.to_json()

    def to_json(self) -> SUB_JSON:
        file_path = str(self.config.path.absolute())
        root_path = str(self.config.root_path.parent.absolute())
        return f"file{file_path.replace(root_path, '')}"

    def validate(self, data: JSON) -> None:
        pass  # no validation
