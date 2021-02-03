from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.output.simulation.mode.mcall.grid.areas import (
    OutputSimulationModeMcAllGridAreas,
)
from antarest.storage_api.filesystem.root.output.simulation.mode.mcall.grid.digest import (
    OutputSimulationModeMcAllGridDigest,
)
from antarest.storage_api.filesystem.root.output.simulation.mode.mcall.grid.links import (
    OutputSimulationModeMcAllGridLinks,
)
from antarest.storage_api.filesystem.root.output.simulation.mode.mcall.grid.thermals import (
    OutputSimulationModeMcAllGridThermals,
)


class OutputSimulationModeMcAllGrid(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "areas": OutputSimulationModeMcAllGridAreas(
                config.next_file("areas.txt")
            ),
            "digest": OutputSimulationModeMcAllGridDigest(
                config.next_file("digest.txt")
            ),
            "links": OutputSimulationModeMcAllGridLinks(
                config.next_file("links.txt")
            ),
            "thermal": OutputSimulationModeMcAllGridThermals(
                config.next_file("thermal.txt")
            ),
        }
        return children
