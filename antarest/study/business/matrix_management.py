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

import itertools
import logging
import operator
from typing import List, Tuple, cast

import numpy as np
import pandas as pd

from antarest.matrixstore.matrix_editor import MatrixEditInstruction, MatrixSlice, Operation
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command_context import CommandContext

logger = logging.getLogger(__name__)


class MatrixManagerError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class MatrixEditError(MatrixManagerError):
    def __init__(self, instruction: MatrixEditInstruction, reason: str) -> None:
        msg = f"Cannot edit matrix using {instruction}: {reason}"
        super().__init__(msg)


class MatrixUpdateError(Exception):
    def __init__(self, operation: Operation, reason: str) -> None:
        msg = f"Cannot apply operation {operation}: {reason}"
        super().__init__(msg)


class MatrixIndexError(MatrixUpdateError):
    def __init__(
        self,
        operation: Operation,
        coordinates: Tuple[int, int],
        exc: Exception,
    ) -> None:
        reason = f"invalid coordinates {coordinates}: {exc}"
        super().__init__(operation, reason)


def update_matrix_content_with_slices(
    matrix_data: pd.DataFrame,
    slices: List[MatrixSlice],
    operation: Operation,
) -> pd.DataFrame:
    mask = pd.DataFrame(np.zeros(matrix_data.shape), dtype=bool)

    for matrix_slice in slices:
        # note: the `.loc` attribute doesn't raise `IndexError`
        mask.loc[
            matrix_slice.row_from : matrix_slice.row_to,
            matrix_slice.column_from : matrix_slice.column_to,
        ] = True

    # noinspection PyTypeChecker
    new_matrix_data = matrix_data.where(mask).apply(operation.compute)
    new_matrix_data[new_matrix_data.isnull()] = matrix_data

    # noinspection PyTypeChecker
    return cast(pd.DataFrame, new_matrix_data.astype(matrix_data.dtypes))


def update_matrix_content_with_coordinates(
    df: pd.DataFrame,
    coordinates: List[Tuple[int, int]],
    operation: Operation,
) -> pd.DataFrame:
    for row, column in coordinates:
        try:
            df.iat[row, column] = operation.compute(df.iat[row, column], use_coords=True)
        except IndexError as exc:
            raise MatrixIndexError(operation, (row, column), exc) from None
    # noinspection PyTypeChecker
    return df.astype(dict(df.dtypes))


def group_by_slices(cells: List[Tuple[int, int]]) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """
    Groups the given cells into rectangular slices based on their coordinates.

    Args:
        cells: A list of tuples representing the coordinates of cells.
            Each tuple contains the (row, col) coordinates of a cell.

    Returns:
        A list of tuples representing the slices.
        Each tuple contains two tuples representing the coordinates of the top-left
        and bottom-right cells of a slice.
    """
    if not cells:
        return []

    # Sort the cells by columns first, and then by rows,
    # since the user typically selects cells by columns.
    cells = sorted(cells, key=lambda p: (p[1], p[0]))

    # Group cells into columns
    column = [cells[0]]
    columns = [column]
    for bottom_most, cell in zip(cells[:-1], cells[1:]):
        if bottom_most[1] == cell[1] and bottom_most[0] == cell[0] - 1:
            # contiguous cell => same column
            column.append(cell)
        else:
            # discontinus cell => new column
            column = [cell]
            columns.append(column)

    # Keep only the top and bottom cells of each column
    columns = [[c[0], c[-1]] for c in columns]

    # Sort the columns by col-axis first and row-axis after
    columns = sorted(columns, key=lambda c: (c[0][0], c[-1][0], c[0][1]))

    # Group columns into slices
    rectangle = [columns[0]]
    rectangles = [rectangle]
    for right_most, column in zip(columns[:-1], columns[1:]):
        if (
            right_most[0][0] == column[0][0]
            and right_most[-1][0] == column[-1][0]
            and right_most[0][1] == column[0][1] - 1
        ):
            # Contiguous column => same slice
            rectangle.append(column)
        else:
            # Discontinuous column => new slice
            rectangle = [column]
            rectangles.append(rectangle)

    # Create the slices by extracting top-left and bottom-right cell coordinates
    return [(r[0][0], r[-1][-1]) for r in rectangles]


def merge_edit_instructions(
    edit_instructions: List[MatrixEditInstruction],
) -> List[MatrixEditInstruction]:
    """
    Merges edit instructions for the same operation and value into
    slice-based edit instructions to reduce computation time when a large
    number of cells are affected.

    This function takes a list of `MatrixEditInstruction` objects and combines
    instructions that have the same operation and value into a single
    instruction that operates on slices of the matrix.

    Args:
        edit_instructions: The list of edit instructions to merge.

    Returns:
        List[MatrixEditInstruction]: The merged edit instructions.
    """
    # First level of triage of editing instructions
    coord_list = []  # those one will be merged
    slices_list = []  # those one are unaffected
    for instr in edit_instructions:
        if instr.coordinates is not None:
            coord_list.append(instr)
        elif instr.slices is not None:
            slices_list.append(instr)
        else:  # pragma: no cover
            raise NotImplementedError(instr)

    # Prepare the result list of instructions
    result_list = slices_list

    # Sort coordinate instructions by operation and values
    by_operation = operator.attrgetter("operation")
    coord_list.sort(key=by_operation)
    for operation, group in itertools.groupby(coord_list, key=by_operation):
        # Collect all coordinates of the group of instructions
        cells = [c for g in group for c in g.coordinates]  # type: ignore

        # Extract the slices to build new "coordinates"/"slices" instructions
        rectangles = group_by_slices(cells)
        coordinates = []
        slices = []
        for rectangle in rectangles:
            top_left = rectangle[0]
            bottom_right = rectangle[-1]
            if top_left == bottom_right:
                # 1-by-1 slices are coordinates
                coordinates.append(top_left)
            else:
                slices.append(
                    MatrixSlice(
                        column_from=top_left[1],
                        column_to=bottom_right[1],
                        row_from=top_left[0],
                        row_to=bottom_right[0],
                    )
                )

        # Add the new instructions to the result
        if coordinates:
            result_list.append(
                MatrixEditInstruction(
                    coordinates=coordinates,
                    operation=operation,
                )
            )
        if slices:
            result_list.append(
                MatrixEditInstruction(
                    slices=slices,
                    operation=operation,
                )
            )

    return result_list


class MatrixManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def update_matrix(
        self,
        study: StudyInterface,
        path: str,
        edit_instructions: List[MatrixEditInstruction],
    ) -> None:
        logger.info(f"Starting matrix update for {study.id}...")
        file_study = study.get_files()
        matrix_service = self._command_context.matrix_service

        matrix_node = file_study.tree.get_node(url=path.split("/"))

        if not isinstance(matrix_node, InputSeriesMatrix):  # pragma: no cover
            raise TypeError(repr(type(matrix_node)))

        try:
            logger.info(f"Loading matrix data from node '{path}'...")
            matrix_df = matrix_node.parse_as_dataframe()
        except ValueError as exc:
            raise MatrixManagerError(f"Cannot parse matrix: {exc}") from exc

        logger.info(f"Merging {len(edit_instructions)} instructions...")
        edit_instructions = merge_edit_instructions(edit_instructions)

        logger.info(f"Processing {len(edit_instructions)} instructions...")
        for instr in edit_instructions:
            try:
                if instr.slices:
                    matrix_df = update_matrix_content_with_slices(
                        matrix_data=matrix_df,
                        slices=instr.slices,
                        operation=instr.operation,
                    )
                elif instr.coordinates:
                    matrix_df = update_matrix_content_with_coordinates(
                        df=matrix_df,
                        coordinates=instr.coordinates,
                        operation=instr.operation,
                    )
                else:  # pragma: no cover
                    raise MatrixEditError(
                        instr,
                        reason="instruction must contain coordinates or slices",
                    )
            except MatrixUpdateError as exc:
                raise MatrixEditError(instr, reason=str(exc)) from None

        logger.info(f"Writing matrix data of shape {matrix_df.shape}...")
        new_matrix_id = matrix_service.create(matrix_df.to_numpy().tolist())

        logger.info(f"Preparing 'ReplaceMatrix' command for path '{path}'...")
        command = [
            ReplaceMatrix(
                target=path,
                matrix=strip_matrix_protocol(new_matrix_id),
                command_context=self._command_context,
                study_version=study.version,
            )
        ]

        logger.info(f"Executing command for study '{study.id}'...")
        study.add_commands(command)

        logger.info("Matrix update done.")
