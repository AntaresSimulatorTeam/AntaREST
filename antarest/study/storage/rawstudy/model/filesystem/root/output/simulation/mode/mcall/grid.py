from pathlib import Path

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import RawFileNode


class OutputSimulationModeMcAllGrid(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        current_path: Path,
    ):
        FolderNode.__init__(self, context, config)
        self.current_path = current_path

    def build(self) -> TREE:
        files = [d.name for d in self.current_path.iterdir()]
        children: TREE = {}
        for file in files:
            children[file] = RawFileNode(self.context, self.config.next_file(f"{file}.txt"))
        return children
