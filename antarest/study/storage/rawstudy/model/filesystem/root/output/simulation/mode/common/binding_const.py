from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    BindingConstraintOutputSeriesMatrix,
)


class OutputSimulationBindingConstraintItem(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
    ):
        super().__init__(context, config)

    def build(self) -> TREE:
        existing_files = [d.stem.replace("binding-constraints-", "") for d in self.config.path.iterdir()]
        children: TREE = {
            f"binding-constraints-{freq}": BindingConstraintOutputSeriesMatrix(
                self.context,
                self.config.next_file(f"binding-constraints-{freq}.txt"),
                MatrixFrequency(freq),
            )
            for freq in existing_files
        }
        return children
