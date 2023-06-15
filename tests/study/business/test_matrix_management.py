from typing import List, Tuple

import pandas as pd
import pytest
from antarest.matrixstore.matrix_editor import (
    MatrixEditInstruction,
    MatrixSlice,
    Operation,
)
from antarest.matrixstore.model import MatrixData
from antarest.study.business.matrix_management import (
    group_by_slices,
    merge_edit_instructions,
    update_matrix_content_with_coordinates,
    update_matrix_content_with_slices,
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
) -> None:
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
) -> None:
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


# alias for shorter code
MEI = MatrixEditInstruction


class TestMergeEditInstructions:
    def test_merge_edit_instructions__coordinates_merged(self) -> None:
        op = Operation(operation="=", value=314)
        instr1 = MEI(coordinates=[(0, 0)], operation=op)
        instr2 = MEI(coordinates=[(1, 1)], operation=op)
        actual = merge_edit_instructions([instr1, instr2])
        assert actual == [MEI(coordinates=[(0, 0), (1, 1)], operation=op)]

    def test_merge_edit_instructions__operations_mixed(self) -> None:
        instr1 = MEI(
            coordinates=[(0, 0)],
            operation=Operation(operation="=", value=314),
        )
        instr2 = MEI(
            coordinates=[(0, 1)],
            operation=Operation(operation="=", value=628),
        )
        instr3 = MEI(
            coordinates=[(1, 0)],
            operation=Operation(operation="/", value=314),
        )
        actual = merge_edit_instructions([instr1, instr2, instr3])
        assert actual == [
            # fmt: off
            MEI(
                coordinates=[(1, 0)],
                operation=Operation(operation="/", value=314.0),
            ),
            MEI(
                coordinates=[(0, 0)],
                operation=Operation(operation="=", value=314.0),
            ),
            MEI(
                coordinates=[(0, 1)],
                operation=Operation(operation="=", value=628.0),
            ),
            # fmt: on
        ]

    def test_merge_edit_instructions__slice_created(self) -> None:
        op = Operation(operation="=", value=314)
        instr1 = MEI(coordinates=[(0, 0)], operation=op)
        instr2 = MEI(coordinates=[(0, 1), (0, 2)], operation=op)
        actual = merge_edit_instructions([instr1, instr2])
        assert actual == [
            # fmt: off
            MEI(
                slices=[MatrixSlice(row_from=0, row_to=2, column_from=0, column_to=0)],
                operation=op,
            )
            # fmt: on
        ]

    def test_merge_edit_instructions__big_column(self) -> None:
        op = Operation(operation="=", value=314)
        instructions = [
            MEI(coordinates=[(0, y)], operation=op) for y in range(8760)
        ]
        actual = merge_edit_instructions(instructions)
        assert actual == [
            # fmt: off
            MEI(
                slices=[MatrixSlice(row_from=0, row_to=8759, column_from=0, column_to=0)],
                operation=op,
            )
            # fmt: on
        ]
