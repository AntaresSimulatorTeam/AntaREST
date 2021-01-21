from pathlib import Path
from typing import Optional, List
from zipfile import ZipFile

from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE, INode


class TestSubNode(INode[int, int, int]):
    def build(self, config: Config) -> "TREE":
        pass

    def __init__(self, value: int):
        self.value = value

    def get(self, url: Optional[List[str]] = None, depth: int = -1) -> int:
        return self.value

    def save(self, data: int, url: Optional[List[str]] = None) -> None:
        self.value = data

    def validate(self, data: int) -> None:
        pass


class TestMiddleNode(FolderNode):
    def __init__(self, config: Config, children: TREE):
        FolderNode.__init__(self, config)
        self.children = children

    def build(self, config: Config) -> TREE:
        return self.children


def extract_sta(project_path: Path, tmp_path: Path) -> Path:
    with ZipFile(project_path / "examples/studies/STA-mini.zip") as zip_output:
        zip_output.extractall(path=tmp_path / "studies")

    return tmp_path / "studies/STA-mini"
