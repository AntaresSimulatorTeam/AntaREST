from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.areas.areas import (
    OutputSimulationModeMcAllAreas,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.grid.grid import (
    OutputSimulationModeMcAllGrid,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.links.links import (
    OutputSimulationModeMcAllLinks,
)


class OutputSimulationModeMcAll(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "areas": OutputSimulationModeMcAllAreas(
                self.context, self.config.next_file("areas")
            ),
            "grid": OutputSimulationModeMcAllGrid(
                self.context, self.config.next_file("grid")
            ),
            "links": OutputSimulationModeMcAllLinks(
                self.context, self.config.next_file("links")
            ),
        }
        return children
