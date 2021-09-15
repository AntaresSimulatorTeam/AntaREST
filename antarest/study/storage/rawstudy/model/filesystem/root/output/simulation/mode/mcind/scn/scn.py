from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcind.scn.areas.areas import (
    OutputSimulationModeMcIndScnAreas,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcind.scn.links.links import (
    OutputSimulationModeMcIndScnLinks,
)


class OutputSimulationModeMcIndScn(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "areas": OutputSimulationModeMcIndScnAreas(
                self.context, self.config.next_file("areas")
            ),
            "links": OutputSimulationModeMcIndScnLinks(
                self.context, self.config.next_file("links")
            ),
        }
        return children
