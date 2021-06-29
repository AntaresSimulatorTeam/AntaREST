from pathlib import Path
from typing import Optional, List
from zipfile import ZipFile

from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE, INode


class TestSubNode(INode[int, int, int]):
    def build(self, config: StudyConfig) -> "TREE":
        pass

    def __init__(self, value: int):
        self.value = value

    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = True,
    ) -> int:
        return self.value

    def save(self, data: int, url: Optional[List[str]] = None) -> None:
        self.value = data

    def check_errors(
        self, data: int, url: Optional[List[str]] = None, raising: bool = False
    ) -> List[str]:
        return []


class TestMiddleNode(FolderNode):
    def __init__(
        self, context: ContextServer, config: StudyConfig, children: TREE
    ):
        FolderNode.__init__(self, context, config)
        self.children = children

    def build(self, config: StudyConfig) -> TREE:
        return self.children


def extract_sta(project_path: Path, tmp_path: Path) -> Path:
    with ZipFile(project_path / "examples/studies/STA-mini.zip") as zip_output:
        zip_output.extractall(path=tmp_path / "studies")

    return tmp_path / "studies/STA-mini"
