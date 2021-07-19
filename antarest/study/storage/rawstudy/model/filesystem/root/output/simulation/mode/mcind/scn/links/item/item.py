from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.context import ContextServer
from antarest.storage.business.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.storage.business.rawstudy.model.filesystem.inode import TREE
from antarest.storage.business.rawstudy.model.filesystem.root.output.simulation.mode.mcind.scn.links.item.values import (
    OutputSimulationModeMcIndScnLinksItemValues as Values,
)


class OutputSimulationModeMcIndScnLinksItem(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
        link: str,
    ):
        FolderNode.__init__(self, context, config)
        self.area = area
        self.link = link

    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            f"values-{timing}": Values(
                self.context,
                config.next_file(f"values-{timing}.txt"),
                timing,
                self.area,
                self.link,
            )
            for timing in config.get_filters_year(self.area, self.link)
        }
        return children
