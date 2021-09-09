from pathlib import Path
from typing import Optional, List
from zipfile import ZipFile

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import (
    TREE,
    INode,
)


class TestSubNode(INode[int, int, int]):
    def normalize(self) -> None:
        pass

    def denormalize(self) -> None:
        pass

    def build(self, config: FileStudyTreeConfig) -> "TREE":
        pass

    def __init__(self, value: int):
        self.value = value

    def get_node(
        self,
        url: Optional[List[str]] = None,
    ) -> INode[int, int, int]:
        return self

    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = True,
        formatted: bool = True,
    ) -> int:
        return self.value

    def save(self, data: int, url: Optional[List[str]] = None) -> None:
        self.value = data

    def delete(self, url: Optional[List[str]] = None) -> None:
        pass

    def check_errors(
        self, data: int, url: Optional[List[str]] = None, raising: bool = False
    ) -> List[str]:
        return []


class TestMiddleNode(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        children: TREE,
    ):
        FolderNode.__init__(self, context, config)
        self.children = children

    def build(self, config: FileStudyTreeConfig) -> TREE:
        return self.children


def extract_sta(project_path: Path, tmp_path: Path) -> Path:
    with ZipFile(project_path / "examples/studies/STA-mini.zip") as zip_output:
        zip_output.extractall(path=tmp_path / "studies")

    return tmp_path / "studies/STA-mini"
