from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.prepro.area.thermal.thermal import (
    InputThermalPreproAreaThermal,
)


class InputThermalPreproArea(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        FolderNode.__init__(self, context, config)
        self.area = area

    def build(self) -> TREE:
        children: TREE = {
            ther: InputThermalPreproAreaThermal(
                self.context, self.config.next_file(ther)
            )
            for ther in self.config.get_thermal_names(self.area)
        }
        return children
