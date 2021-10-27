from typing import List

from antarest.matrixstore.model import MatrixData

credit_modulations: List[List[MatrixData]] = [[1] * 101] * 2
inflow_pattern: List[List[MatrixData]] = [[1]] * 365
max_power: List[List[MatrixData]] = [[0, 24, 0, 24]] * 365
reservoir: List[List[MatrixData]] = [[0, 0.5, 1]] * 365
