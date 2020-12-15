from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.reserves.area import (
    InputReservesArea,
)


class InputReserves(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            a: InputReservesArea(config.next_file(f"{a}.txt"))
            for a in config.area_names
        }
        return children
