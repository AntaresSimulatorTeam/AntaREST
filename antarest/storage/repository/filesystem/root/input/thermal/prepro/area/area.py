from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.thermal.prepro.area.thermal.thermal import (
    InputThermalPreproAreaThermal,
)


class InputThermalPreproArea(FolderNode):
    def __init__(self, context: ContextServer, config: StudyConfig, area: str):
        FolderNode.__init__(self, context, config)
        self.area = area

    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            ther: InputThermalPreproAreaThermal(
                self.context, config.next_file(ther)
            )
            for ther in config.get_thermal_names(self.area)
        }
        return children
