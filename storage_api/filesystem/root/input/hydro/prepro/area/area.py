from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.input.hydro.prepro.area.energy import (
    InputHydroPreproAreaEnergy,
)
from storage_api.filesystem.root.input.hydro.prepro.area.prepro import (
    InputHydroPreproAreaPrepro,
)


class InputHydroPreproArea(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "energy": InputHydroPreproAreaEnergy(
                config.next_file("energy.txt")
            ),
            "prepro": InputHydroPreproAreaPrepro(
                config.next_file("prepro.ini")
            ),
        }
        return children
