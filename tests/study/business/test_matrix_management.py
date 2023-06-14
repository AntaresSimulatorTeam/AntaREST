from typing import List, Tuple

import pandas as pd
import pytest
from antarest.matrixstore.business.matrix_editor import MatrixSlice, Operation
from antarest.matrixstore.model import MatrixData
from antarest.study.business.matrix_management import (
    update_matrix_content_with_coordinates,
    update_matrix_content_with_slices,
    group_by_slices,
)


@pytest.mark.unit_test
@pytest.mark.parametrize(
    "slices, operation, expected_result",
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
def test_update_matrix_content_with_slices(
    slices: List[MatrixSlice],
    operation: Operation,
    expected_result: List[List[MatrixData]],
):
    matrix_data = pd.DataFrame([[-1] * 5] * 5, dtype=float)

    output_matrix = update_matrix_content_with_slices(
        matrix_data=matrix_data, slices=slices, operation=operation
    )

    assert output_matrix.equals(
        pd.DataFrame(expected_result).astype(matrix_data.dtypes)
    )


@pytest.mark.unit_test
@pytest.mark.parametrize(
    "coords, operation, expected_result",
    [
        (
            [
                (0, 0),
                (2, 2),
                (2, 3),
                (3, 3),
                (3, 2),
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
                (1, 0),
                (1, 1),
                (1, 2),
                (1, 3),
                (1, 4),
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
                (0, 1),
                (1, 1),
                (2, 1),
                (3, 1),
                (4, 1),
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
            [(2, 1)],
            Operation(operation="/", value=2),
            [
                [-1, -1, -1, -1, -1],
                [-1, -1, -1, -1, -1],
                [-1, -0.5, -1, -1, -1],
                [-1, -1, -1, -1, -1],
                [-1, -1, -1, -1, -1],
            ],
        ),
        (
            [(1, 1)],
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
            [(4, 4)],
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
def test_update_matrix_content_with_coordinates(
    coords: List[Tuple[int, int]],
    operation: Operation,
    expected_result: List[List[MatrixData]],
):
    matrix_data = pd.DataFrame([[-1] * 5] * 5, dtype=float)

    output_matrix = update_matrix_content_with_coordinates(
        df=matrix_data, coordinates=coords, operation=operation
    )

    assert output_matrix.equals(
        pd.DataFrame(expected_result).astype(matrix_data.dtypes)
    )


class TestGroupBySlices:
    @pytest.mark.parametrize(
        "cells, expected",
        [
            # fmt: off
            pytest.param([], [], id="empty-cells-list"),
            pytest.param(
                [(3, 7)],
                [((3, 7), (3, 7))],
                id="unique-cell",
            ),
            pytest.param(
                [(0, 1), (0, 2)],
                [((0, 1), (0, 2))],
                id="simple-vertical-merge",
            ),
            pytest.param(
                [(2, 1), (3, 1)],
                [((2, 1), (3, 1))],
                id="simple-horizontal-merge",
            ),
            pytest.param(
                [(2, 4), (2, 5), (3, 4), (3, 5), (4, 4), (4, 5)],
                [((2, 4), (4, 5))],
                id="rectangular-merge",
            ),
            pytest.param(
                [(1, 1), (2, 2)],
                [((1, 1), (1, 1)), ((2, 2), (2, 2))],
                id="simple-disjonction",
            ),
            pytest.param(
                [
                    (0, 0), (1, 0), (2, 0),
                    (0, 1), (2, 1),
                    (0, 2), (1, 2), (2, 2),
                ],
                [
                    ((1, 0), (1, 0)),
                    ((0, 0), (0, 2)),
                    ((2, 0), (2, 2)),
                    ((1, 2), (1, 2)),
                ],
                id="square-with-centered-hole",
            ),
            # fmt: on
        ],
    )
    def test_group_by_slices(
        self,
        cells: List[Tuple[int, int]],
        expected: List[Tuple[Tuple[int, int], Tuple[int, int]]],
    ) -> None:
        actual = group_by_slices(cells)
        assert actual == expected
