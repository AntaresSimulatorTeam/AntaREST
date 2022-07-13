from typing import List

import pandas as pd
import pytest

from antarest.matrixstore.business.matrix_editor import (
    Operation,
    MatrixSlice,
    MatrixEditor,
)
from antarest.matrixstore.model import MatrixData


@pytest.mark.unit_test
@pytest.mark.parametrize(
    "slices,operation,expected_result",
    [
        (
            [
                MatrixSlice(row_from=0, column_from=0),
                MatrixSlice(row_from=2, row_to=3, column_from=2, column_to=3),
            ],
            Operation(operation="+", value=2),
            [
                [1, -1, -1, -1, -1],
                [-1, -1, -1, -1, -1],
                [-1, -1, 1, 1, -1],
                [-1, -1, 1, 1, -1],
                [-1, -1, -1, -1, -1],
            ],
        ),
        (
            [
                MatrixSlice(row_from=1, column_from=0, column_to=5),
            ],
            Operation(operation="-", value=1),
            [
                [-1, -1, -1, -1, -1],
                [-2, -2, -2, -2, -2],
                [-1, -1, -1, -1, -1],
                [-1, -1, -1, -1, -1],
                [-1, -1, -1, -1, -1],
            ],
        ),
        (
            [
                MatrixSlice(row_from=0, row_to=5, column_from=1),
            ],
            Operation(operation="*", value=3),
            [
                [-1, -3, -1, -1, -1],
                [-1, -3, -1, -1, -1],
                [-1, -3, -1, -1, -1],
                [-1, -3, -1, -1, -1],
                [-1, -3, -1, -1, -1],
            ],
        ),
        (
            [
                MatrixSlice(row_from=0, row_to=5, column_from=0, column_to=5),
            ],
            Operation(operation="/", value=2),
            [
                [-0.5, -0.5, -0.5, -0.5, -0.5],
                [-0.5, -0.5, -0.5, -0.5, -0.5],
                [-0.5, -0.5, -0.5, -0.5, -0.5],
                [-0.5, -0.5, -0.5, -0.5, -0.5],
                [-0.5, -0.5, -0.5, -0.5, -0.5],
            ],
        ),
        (
            [
                MatrixSlice(row_from=1, column_from=1),
            ],
            Operation(operation="ABS", value=2),
            [
                [-1, -1, -1, -1, -1],
                [-1, 1, -1, -1, -1],
                [-1, -1, -1, -1, -1],
                [-1, -1, -1, -1, -1],
                [-1, -1, -1, -1, -1],
            ],
        ),
        (
            [
                MatrixSlice(row_from=4, column_from=4),
            ],
            Operation(operation="=", value=42),
            [
                [-1, -1, -1, -1, -1],
                [-1, -1, -1, -1, -1],
                [-1, -1, -1, -1, -1],
                [-1, -1, -1, -1, -1],
                [-1, -1, -1, -1, 42],
            ],
        ),
    ],
)
def test_matrix_editor(
    slices: List[MatrixSlice],
    operation: Operation,
    expected_result: List[List[MatrixData]],
):
    matrix_data = pd.DataFrame([[-1] * 5] * 5, dtype=float)

    output_matrix = MatrixEditor.update_matrix_content_with_slices(
        matrix_data=matrix_data, slices=slices, operation=operation
    )

    assert output_matrix.equals(
        pd.DataFrame(expected_result).astype(matrix_data.dtypes)
    )
