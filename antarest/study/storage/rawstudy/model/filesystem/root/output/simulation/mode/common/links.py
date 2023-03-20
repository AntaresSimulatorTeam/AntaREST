from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.link import (
    OutputSimulationLinkItem,
)


class _OutputSimulationModeMcAllLinksBis(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
        mc_all: bool,
    ):
        FolderNode.__init__(self, context, config)
        self.area = area
        self.mc_all = mc_all

    def build(self) -> TREE:
        children: TREE = {}
        for link in self.config.get_links(self.area):
            name = f"{self.area} - {link}"
            children[link] = OutputSimulationLinkItem(
                self.context,
                self.config.next_file(name),
                self.area,
                link,
                mc_all=self.mc_all,
            )
        return children


class OutputSimulationLinks(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        mc_all: bool = True,
    ):
        super().__init__(context, config)
        self.mc_all = mc_all

    def build(self) -> TREE:
        children: TREE = {}

        for area in self.config.area_names():
            children[area] = _OutputSimulationModeMcAllLinksBis(
                self.context, self.config, area, self.mc_all
            )

        return children
