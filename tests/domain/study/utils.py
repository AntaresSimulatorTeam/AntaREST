from pathlib import Path
from typing import Optional, List
from zipfile import ZipFile

from api_iso_antares.domain.study.inode import TREE, INode
from api_iso_antares.domain.study.folder_node import FolderNode


class TestSubNode(INode[int]):
    def __init__(self, value: int):
        self.value = value

    def get(self, url: Optional[List[str]] = None) -> int:
        return self.value

    def save(self, data: int, url: Optional[List[str]] = None) -> None:
        self.value = data

    def validate(self, data: int) -> None:
        pass


class TestFolderNode(FolderNode):
    def __init__(self, children: TREE):
        self.children = children


def extract_sta(project_path: Path, tmp_path: Path) -> Path:
    with ZipFile(project_path / "examples/studies/STA-mini.zip") as zip_output:
        zip_output.extractall(path=tmp_path / "studies")

    return tmp_path / "studies/STA-mini"
