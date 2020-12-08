from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.input.reserves.area import (
    InputReservesArea,
)


class InputReserves(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            a: InputReservesArea(config.next_file(f"{a}.txt"))
            for a in config.area_names
        }
        FolderNode.__init__(self, children)
