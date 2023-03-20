from typing import List, TypedDict

from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import (
    MatrixFrequency,
)


class MatrixInfo(TypedDict, total=False):
    name: str
    freq: MatrixFrequency
    start_version: int


# noinspection SpellCheckingInspection
MATRICES_INFO: List[MatrixInfo] = [
    {
        "name": "maxpower",
        "freq": MatrixFrequency.HOURLY,
        "start_version": 0,
    },
    {
        "name": "reservoir",
        "freq": MatrixFrequency.DAILY,
        "start_version": 0,
    },
    {
        "name": "inflowPattern",
        "freq": MatrixFrequency.HOURLY,
        "start_version": 650,
    },
    {
        "name": "creditmodulations",
        "freq": MatrixFrequency.HOURLY,
        "start_version": 650,
    },
    {
        "name": "waterValues",
        "freq": MatrixFrequency.DAILY,
        "start_version": 650,
    },
]


class InputHydroCommonCapacity(FolderNode):
    def build(self) -> TREE:
        children: TREE = {}
        for info in MATRICES_INFO:
            if self.config.version >= info["start_version"]:
                for area in self.config.area_names():
                    name = f"{info['name']}_{area}"
                    children[name] = InputSeriesMatrix(
                        self.context,
                        self.config.next_file(f"{name}.txt"),
                        freq=info["freq"],
                    )
        return children
