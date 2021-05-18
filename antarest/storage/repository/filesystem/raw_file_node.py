import shutil
from typing import List, Optional

from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.inode import INode, TREE


class RawFileNode(INode[str, str, str]):
    def __init__(self, config: StudyConfig):
        self.config = config

    def build(self, config: StudyConfig) -> TREE:
        pass  # end node has nothing to build

    def get(self, url: Optional[List[str]] = None, depth: int = -1) -> str:
        self._assert_url(url)

        file_path = "/".join(self.config.path.absolute().parts)
        root_path = "/".join(self.config.root_path.parent.absolute().parts)
        file_relative = file_path.replace(root_path, "")
        return f"file{file_relative}"

    def save(self, data: str, url: Optional[List[str]] = None) -> None:
        self._assert_url(url)

        path = self.config.root_path.parent / data[len("file/") :]

        if path != self.config.path:
            self.config.path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, self.config.path)

    def check_errors(
        self, data: str, url: Optional[List[str]] = None, raising: bool = False
    ) -> List[str]:
        if not self.config.path.exists():
            msg = f"{self.config.path} not exist"
            if raising:
                raise ValueError(msg)
            return [msg]
        return []
