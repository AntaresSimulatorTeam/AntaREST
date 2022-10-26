from antarest.study.storage.rawstudy.model.filesystem.common.area_matrix_list import (
    AreaMatrixList,
)
from antarest.study.storage.rawstudy.model.filesystem.common.prepro import (
    InputPrepro,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import (
    default_scenario_hourly,
)


class InputWind(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "prepro": InputPrepro(
                self.context, self.config.next_file("prepro")
            ),
            "series": AreaMatrixList(
                self.context,
                self.config.next_file("series"),
                prefix="wind_",
                additional_matrix_params={
                    "default_empty": default_scenario_hourly
                },
            ),
        }
        return children
