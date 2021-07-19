from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.storage.business.rawstudy.model.filesystem.inode import TREE
from antarest.storage.business.rawstudy.model.filesystem.root.output.simulation.mode.mcind.scn.areas.areas import (
    OutputSimulationModeMcIndScnAreas,
)
from antarest.storage.business.rawstudy.model.filesystem.root.output.simulation.mode.mcind.scn.links.links import (
    OutputSimulationModeMcIndScnLinks,
)


class OutputSimulationModeMcIndScn(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "areas": OutputSimulationModeMcIndScnAreas(
                self.context, config.next_file("areas")
            ),
            "links": OutputSimulationModeMcIndScnLinks(
                self.context, config.next_file("links")
            ),
        }
        return children
