from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


class InputHydroCommonCapacity(FolderNode):
    def build(self) -> TREE:
        children: TREE = dict()
        for area in self.config.area_names():
            config_filenames = [
                "maxpower",
                "reservoir",
            ]
            if self.config.version >= 650:
                config_filenames.append("inflowPattern")
                config_filenames.append("creditmodulations")
                config_filenames.append("waterValues")
            for file in config_filenames:
                name = f"{file}_{area}"
                children[name] = InputSeriesMatrix(
                    self.context, self.config.next_file(f"{name}.txt")
                )
        return children
