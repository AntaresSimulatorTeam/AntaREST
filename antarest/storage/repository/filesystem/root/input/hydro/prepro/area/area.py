from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.hydro.prepro.area.energy import (
    InputHydroPreproAreaEnergy,
)
from antarest.storage.repository.filesystem.root.input.hydro.prepro.area.prepro import (
    InputHydroPreproAreaPrepro,
)


class InputHydroPreproArea(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "energy": InputHydroPreproAreaEnergy(
                self.context, config.next_file("energy.txt")
            ),
            "prepro": InputHydroPreproAreaPrepro(
                self.context, config.next_file("prepro.ini")
            ),
        }
        return children
