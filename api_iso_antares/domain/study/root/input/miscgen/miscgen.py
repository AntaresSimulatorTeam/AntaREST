from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.input.miscgen.area import (
    InputMiscGenArea,
)


class InputMiscGen(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            f"miscgen-{a}": InputMiscGenArea(
                config.next_file(f"miscgen-{a}.txt")
            )
            for a in config.area_names
        }
        FolderNode.__init__(self, children)
