from pathlib import Path

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import LinkOutputSeriesMatrix


class OutputSimulationLinkItem(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
        link: str,
        current_path: Path,
        mc_all: bool = True,
    ):
        FolderNode.__init__(self, context, config)
        self.area = area
        self.link = link
        self.current_path = current_path
        self.mc_all = mc_all

    def build(self) -> TREE:
        children: TREE = {}
        freq: MatrixFrequency
        for freq in MatrixFrequency:
            if (self.current_path / f"values-{freq}.txt").exists():
                children[f"values-{freq}"] = LinkOutputSeriesMatrix(
                    self.context,
                    self.config.next_file(f"values-{freq}.txt"),
                    freq,
                    self.area,
                    self.link,
                )
            if self.mc_all and (self.current_path / f"id-{freq}.txt").exists():
                children[f"id-{freq}"] = LinkOutputSeriesMatrix(
                    self.context,
                    self.config.next_file(f"id-{freq}.txt"),
                    freq,
                    self.area,
                    self.link,
                )

        return children
