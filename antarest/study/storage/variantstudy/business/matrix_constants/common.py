from typing import List

from antarest.matrixstore.model import MatrixData

NULL_MATRIX: List[List[MatrixData]] = [[]]
NULL_SCENARIO_MATRIX: List[List[MatrixData]] = [[0.0]] * 8760
FIXED_4_COLUMNS = [[0.0, 0.0, 0.0, 0.0]] * 8760
FIXED_8_COLUMNS = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]] * 8760
