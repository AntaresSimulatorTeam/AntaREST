from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.input.reserves.area import (
    InputReservesArea,
)


class InputReserves(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            a: InputReservesArea(config.next_file(f"{a}.txt"))
            for a in config.area_names()
        }
        return children
