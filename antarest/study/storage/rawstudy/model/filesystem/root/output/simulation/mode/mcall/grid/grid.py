from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.storage.business.rawstudy.model.filesystem.inode import TREE
from antarest.storage.business.rawstudy.model.filesystem.root.output.simulation.mode.mcall.grid.areas import (
    OutputSimulationModeMcAllGridAreas,
)
from antarest.storage.business.rawstudy.model.filesystem.root.output.simulation.mode.mcall.grid.digest import (
    OutputSimulationModeMcAllGridDigest,
)
from antarest.storage.business.rawstudy.model.filesystem.root.output.simulation.mode.mcall.grid.links import (
    OutputSimulationModeMcAllGridLinks,
)
from antarest.storage.business.rawstudy.model.filesystem.root.output.simulation.mode.mcall.grid.thermals import (
    OutputSimulationModeMcAllGridThermals,
)


class OutputSimulationModeMcAllGrid(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "areas": OutputSimulationModeMcAllGridAreas(
                self.context, config.next_file("areas.txt")
            ),
            "digest": OutputSimulationModeMcAllGridDigest(
                self.context, config.next_file("digest.txt")
            ),
            "links": OutputSimulationModeMcAllGridLinks(
                self.context, config.next_file("links.txt")
            ),
            "thermal": OutputSimulationModeMcAllGridThermals(
                self.context, config.next_file("thermal.txt")
            ),
        }
        return children
