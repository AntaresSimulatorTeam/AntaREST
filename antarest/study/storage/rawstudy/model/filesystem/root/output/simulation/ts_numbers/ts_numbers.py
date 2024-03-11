from antarest.study.storage.rawstudy.model.filesystem.common.area_matrix_list import (
    AreaMatrixList,
    AreaMultipleMatrixList,
    BindingConstraintMatrixList,
    ThermalMatrixList,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.ts_numbers.ts_numbers_data import (
    TsNumbersVector,
)


class OutputSimulationTsNumbers(FolderNode):
    """
    Represents a folder structure, which contains several time series folders
    (one for each generator type: "hydro", "load", "solar" and "wind")
    and a specific folder structure for the thermal clusters (one for each area).

    Example of tree structure:

    .. code-block:: text

       output/20230323-1540adq/ts-numbers/
       ├── hydro
       │   ├── at.txt
       │   ├── ch.txt
       │   ├── pompage.txt
       │   └── turbinage.txt
       ├── load
       │   ├── at.txt
       │   ├── ch.txt
       │   ├── pompage.txt
       │   └── turbinage.txt
       ├── solar
       │   ├── at.txt
       │   ├── ch.txt
       │   ├── pompage.txt
       │   └── turbinage.txt
       ├── thermal
       │   ├── at [...]
       │   ├── ch [...]
       │   ├── pompage [...]
       │   └── turbinage [...]
       ├── wind
       │   ├── at.txt
       │   ├── ch.txt
       │   ├── pompage.txt
       │   └── turbinage.txt
       ├── bindingconstraints
           ├── group_1.txt
           ├── group_2.txt
           └── [...]
    """

    def build(self) -> TREE:
        children: TREE = {
            "hydro": AreaMatrixList(
                self.context,
                self.config.next_file("hydro"),
                matrix_class=TsNumbersVector,
            ),
            "load": AreaMatrixList(
                self.context,
                self.config.next_file("load"),
                matrix_class=TsNumbersVector,
            ),
            "solar": AreaMatrixList(
                self.context,
                self.config.next_file("solar"),
                matrix_class=TsNumbersVector,
            ),
            "wind": AreaMatrixList(
                self.context,
                self.config.next_file("wind"),
                matrix_class=TsNumbersVector,
            ),
            "thermal": AreaMultipleMatrixList(
                self.context,
                self.config.next_file("thermal"),
                ThermalMatrixList,
                TsNumbersVector,
            ),
        }
        if self.config.version >= 870:
            children["bindingconstraints"] = BindingConstraintMatrixList(
                self.context, self.config.next_file("bindingconstraints"), matrix_class=TsNumbersVector
            )
        return children
