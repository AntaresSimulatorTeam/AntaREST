from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.areas.item.area import (
    OutputSimulationModeMcAllAreasArea as Area,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.areas.item.set import (
    OutputSimulationModeMcAllAreasSet as Set,
)


class OutputSimulationModeMcAllAreas(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            a: Area(self.context, self.config.next_file(a), area=a)
            for a in self.config.area_names()
        }

        for s in self.config.set_names():
            children[f"@ {s}"] = Set(
                self.context, self.config.next_file(f"@ {s}"), set=s
            )
        return children
