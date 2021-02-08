from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.folder_node import FolderNode
from antarest.storage.filesystem.inode import TREE
from antarest.storage.filesystem.root.input.reserves.area import (
    InputReservesArea,
)


class InputReserves(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            a: InputReservesArea(config.next_file(f"{a}.txt"))
            for a in config.area_names()
        }
        return children
