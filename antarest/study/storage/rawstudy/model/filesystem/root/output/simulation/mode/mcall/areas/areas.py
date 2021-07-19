from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.storage.business.rawstudy.model.filesystem.inode import TREE
from antarest.storage.business.rawstudy.model.filesystem.root.output.simulation.mode.mcall.areas.item.area import (
    OutputSimulationModeMcAllAreasArea as Area,
)
from antarest.storage.business.rawstudy.model.filesystem.root.output.simulation.mode.mcall.areas.item.set import (
    OutputSimulationModeMcAllAreasSet as Set,
)


class OutputSimulationModeMcAllAreas(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            a: Area(self.context, config.next_file(a), area=a)
            for a in config.area_names()
        }

        for s in config.set_names():
            children[f"@ {s}"] = Set(
                self.context, config.next_file(f"@ {s}"), set=s
            )
        return children
