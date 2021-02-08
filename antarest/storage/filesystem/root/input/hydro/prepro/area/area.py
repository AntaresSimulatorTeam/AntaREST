from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.folder_node import FolderNode
from antarest.storage.filesystem.inode import TREE
from antarest.storage.filesystem.root.input.hydro.prepro.area.energy import (
    InputHydroPreproAreaEnergy,
)
from antarest.storage.filesystem.root.input.hydro.prepro.area.prepro import (
    InputHydroPreproAreaPrepro,
)


class InputHydroPreproArea(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "energy": InputHydroPreproAreaEnergy(
                config.next_file("energy.txt")
            ),
            "prepro": InputHydroPreproAreaPrepro(
                config.next_file("prepro.ini")
            ),
        }
        return children
