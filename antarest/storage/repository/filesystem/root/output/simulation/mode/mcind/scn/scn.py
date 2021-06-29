from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcind.scn.areas.areas import (
    OutputSimulationModeMcIndScnAreas,
)
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcind.scn.links.links import (
    OutputSimulationModeMcIndScnLinks,
)


class OutputSimulationModeMcIndScn(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "areas": OutputSimulationModeMcIndScnAreas(
                self.context, config.next_file("areas")
            ),
            "links": OutputSimulationModeMcIndScnLinks(
                self.context, config.next_file("links")
            ),
        }
        return children
