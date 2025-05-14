# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.
from typing_extensions import override

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


# noinspection SpellCheckingInspection
class OutputSimulationTsNumbers(FolderNode):
    """
    Represents a folder structure, which contains several time series folders
    (one for each generator type: "hydro", "load", "solar" and "wind")
    and a specific folder structure for the thermal clusters (one for each area).

    Since v8.7, it also contains a folder for the binding constraints.

    Example of tree structure:

    .. code-block:: text

       output/20230323-1540adq/ts-numbers/
       ├── bindingconstraints
       │   ├── group_1.txt
       │   ├── group_2.txt
       │   └── [...]
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
       └── wind
           ├── at.txt
           ├── ch.txt
           ├── pompage.txt
           └── turbinage.txt
    """

    @override
    def build(self) -> TREE:
        children: TREE = {}
        for output_type in ["hydro", "load", "solar", "wind"]:
            if (self.config.path / output_type).exists():
                children[output_type] = AreaMatrixList(
                    self.matrix_mapper,
                    self.config.next_file(output_type),
                    matrix_class=TsNumbersVector,
                )
        if (self.config.path / "bindingconstraints").exists():
            children["bindingconstraints"] = BindingConstraintMatrixList(
                self.matrix_mapper, self.config.next_file("bindingconstraints"), matrix_class=TsNumbersVector
            )
        if (self.config.path / "thermal").exists():
            children["thermal"] = AreaMultipleMatrixList(
                self.matrix_mapper,
                self.config.next_file("thermal"),
                ThermalMatrixList,
                TsNumbersVector,
            )
        return children
