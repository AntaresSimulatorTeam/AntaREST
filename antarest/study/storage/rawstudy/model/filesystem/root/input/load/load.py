from antarest.study.storage.rawstudy.model.filesystem.common.area_matrix_list import AreaMatrixList
from antarest.study.storage.rawstudy.model.filesystem.common.prepro import InputPrepro
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import default_scenario_hourly


class InputLoad(FolderNode):
    """
    Represents a folder structure, which contains a "prepro" and a time series structure.

    Example of tree structure:

    .. code-block:: text

       input/load/
       ├── prepro
       │   ├── correlation.ini
       │   ├── store_in
       │   │   ├── conversion.txt
       │   │   ├── data.txt
       │   │   ├── k.txt
       │   │   ├── settings.ini
       │   │   └── translation.txt
       │   └── store_out
       │       ├── conversion.txt
       │       ├── data.txt
       │       ├── k.txt
       │       ├── settings.ini
       │       └── translation.txt
       └── series
           ├── load_store_in.txt
           └── load_store_out.txt
    """

    def build(self) -> TREE:
        children: TREE = {
            "prepro": InputPrepro(self.context, self.config.next_file("prepro")),
            "series": AreaMatrixList(
                self.context,
                self.config.next_file("series"),
                prefix="load_",
                additional_matrix_params={"default_empty": default_scenario_hourly},
            ),
        }
        return children
