import typing as t
from pathlib import Path

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.link import (
    OutputSimulationLinkItem,
)


class _OutputSimulationModeMcAllLinksBis(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area_from: str,
        link_names: t.List[str],
        current_path: Path,
        mc_all: bool,
    ):
        FolderNode.__init__(self, context, config)
        self.area_from = area_from
        self.link_names = link_names
        self.current_path = current_path
        self.mc_all = mc_all

    def build(self) -> TREE:
        children: TREE = {}
        for link_name in self.link_names:
            link = link_name.split(" - ")[1]
            children[link] = OutputSimulationLinkItem(
                self.context,
                self.config.next_file(link_name),
                self.area_from,
                link,
                self.current_path / link_name,
                mc_all=self.mc_all,
            )
        return children


class OutputSimulationLinks(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        current_path: Path,
        mc_all: bool = False,
    ):
        super().__init__(context, config)
        self.current_path = current_path
        self.mc_all = mc_all

    def build(self) -> TREE:
        children: TREE = {}

        links = [d.name for d in self.current_path.iterdir()]
        areas: t.Dict[str, t.List[str]] = {}
        for link in links:
            areas.setdefault(link.split(" - ")[0], []).append(link)
        for area_from, link_names in areas.items():
            children[area_from] = _OutputSimulationModeMcAllLinksBis(
                self.context, self.config, area_from, link_names, self.current_path, self.mc_all
            )

        return children
