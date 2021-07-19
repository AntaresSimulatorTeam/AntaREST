from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcall.areas.areas import (
    OutputSimulationModeMcAllAreas,
)
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcall.grid.grid import (
    OutputSimulationModeMcAllGrid,
)
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcall.links.links import (
    OutputSimulationModeMcAllLinks,
)


class OutputSimulationModeMcAll(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "areas": OutputSimulationModeMcAllAreas(
                self.context, config.next_file("areas")
            ),
            "grid": OutputSimulationModeMcAllGrid(
                self.context, config.next_file("grid")
            ),
            "links": OutputSimulationModeMcAllLinks(
                self.context, config.next_file("links")
            ),
        }
        return children
