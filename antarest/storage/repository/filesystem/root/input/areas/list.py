from typing import Optional, List

from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.inode import INode, TREE


class InputAreasList(INode[List[str], List[str], List[str]]):
    def __init__(self, config: StudyConfig):
        self.config = config

    def build(self, config: StudyConfig) -> TREE:
        pass  # End of root. No build

    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> List[str]:
        lines = self.config.path.read_text().lower().split("\n")
        return [l.strip() for l in lines if l.strip()]

    def save(self, data: List[str], url: Optional[List[str]] = None) -> None:
        self.config.path.write_text("\n".join(data).upper())

    def check_errors(
        self,
        data: List[str],
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:

        errors = []
        if any(a not in data for a in self.config.area_names()):
            errors.append(
                f"list.txt should have {self.config.area_names()} nodes but given {data}"
            )
        return errors
