from pathlib import Path

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import AreaOutputSeriesMatrix


class OutputSimulationSet(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        current_path: Path,
        set: str,
    ):
        FolderNode.__init__(self, context, config)
        self.current_path = current_path
        self.set = set

    def build(self) -> TREE:
        children: TREE = {}
        possible_outputs = ["id", "values"]
        freq: MatrixFrequency
        for freq in MatrixFrequency:
            for output_type in possible_outputs:
                file_name = f"{output_type}-{freq}.txt"
                if (self.current_path / file_name).exists():
                    children[f"{output_type}-{freq}"] = AreaOutputSeriesMatrix(
                        self.context,
                        self.config.next_file(file_name),
                        freq,
                        self.set,
                    )

        return children
