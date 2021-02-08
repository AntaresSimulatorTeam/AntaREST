from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.folder_node import FolderNode
from antarest.storage.filesystem.inode import TREE
from antarest.storage.filesystem.root.output.simulation.mode.mcind.scn.areas.areas import (
    OutputSimulationModeMcIndScnAreas,
)
from antarest.storage.filesystem.root.output.simulation.mode.mcind.scn.links.links import (
    OutputSimulationModeMcIndScnLinks,
)


class OutputSimulationModeMcIndScn(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "areas": OutputSimulationModeMcIndScnAreas(
                config.next_file("areas")
            ),
            "links": OutputSimulationModeMcIndScnLinks(
                config.next_file("links")
            ),
        }
        return children
