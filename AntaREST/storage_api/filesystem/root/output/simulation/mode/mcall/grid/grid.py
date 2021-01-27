from AntaREST.storage_api.filesystem.config.model import Config
from AntaREST.storage_api.filesystem.folder_node import FolderNode
from AntaREST.storage_api.filesystem.inode import TREE
from AntaREST.storage_api.filesystem.root.output.simulation.mode.mcall.grid.areas import (
    OutputSimulationModeMcAllGridAreas,
)
from AntaREST.storage_api.filesystem.root.output.simulation.mode.mcall.grid.digest import (
    OutputSimulationModeMcAllGridDigest,
)
from AntaREST.storage_api.filesystem.root.output.simulation.mode.mcall.grid.links import (
    OutputSimulationModeMcAllGridLinks,
)
from AntaREST.storage_api.filesystem.root.output.simulation.mode.mcall.grid.thermals import (
    OutputSimulationModeMcAllGridThermals,
)


class OutputSimulationModeMcAllGrid(FolderNode):
    def build(self, config: Config) -> TREE:
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
