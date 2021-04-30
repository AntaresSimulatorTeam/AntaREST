from typing import Optional, List

from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.inode import INode, V, S, G


class OutputSeriesMatrix(INode):
    def build(self, config: StudyConfig) -> "TREE":
        pass

    def get(self, url: Optional[List[str]] = None, depth: int = -1) -> G:
        pass

    def save(self, data: S, url: Optional[List[str]] = None) -> None:
        pass

    def check_errors(
        self, data: V, url: Optional[List[str]] = None, raising: bool = False
    ) -> List[str]:
        pass
