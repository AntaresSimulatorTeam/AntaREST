from typing import List, Tuple

import numpy as np
import pandas as pd  # type:ignore
from antarest.matrixstore.business.matrix_editor import (
    MatrixEditInstructionDTO,
    MatrixSlice,
    Operation,
)
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.utils import is_managed
from antarest.study.storage.variantstudy.business.utils import (
    strip_matrix_protocol,
)
from antarest.study.storage.variantstudy.model.command.replace_matrix import (
    ReplaceMatrix,
)


class MatrixManagerError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class MatrixEditError(MatrixManagerError):
    def __init__(
        self, instruction: MatrixEditInstructionDTO, reason: str
    ) -> None:
        msg = f"Cannot edit matrix using {instruction}: {reason}"
        super().__init__(msg)


class MatrixUpdateError(Exception):
    def __init__(self, operation: Operation, reason: str) -> None:
        msg = f"Cannot apply operation {operation}: {reason}"
        super().__init__(msg)


class MatrixSliceError(MatrixUpdateError):
    def __init__(
        self, operation: Operation, matrix_slice: MatrixSlice, exc: Exception
    ) -> None:
        reason = f"invalid slice {matrix_slice}: {exc}"
        super().__init__(operation, reason)


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
        try:
            mask.loc[
                matrix_slice.row_from : matrix_slice.row_to,
                matrix_slice.column_from : matrix_slice.column_to,
            ] = True
        except IndexError as exc:
            raise MatrixSliceError(operation, matrix_slice, exc) from None

    new_matrix_data = matrix_data.where(mask).apply(operation.compute)
    new_matrix_data[new_matrix_data.isnull()] = matrix_data

    return new_matrix_data.astype(matrix_data.dtypes)


def update_matrix_content_with_coordinates(
    df: pd.DataFrame,
    coordinates: List[Tuple[int, int]],
    operation: Operation,
) -> pd.DataFrame:
    for row, column in coordinates:
        try:
            df.iat[row, column] = operation.compute(
                df.iat[row, column], use_coords=True
            )
        except IndexError as exc:
            raise MatrixIndexError(operation, (row, column), exc) from None
    return df.astype(df.dtypes)


def group_by_slices(
    cells: List[Tuple[int, int]]
) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """
    Groups the given cells into rectangular slices based on their coordinates.

    Args:
        cells: A list of tuples representing the coordinates of cells.
            Each tuple contains the (x, y) coordinates of a cell.

    Returns:
        A list of tuples representing the slices.
        Each tuple contains two tuples representing the coordinates of the top-left
        and bottom-right cells of a slice.
    """
    if not cells:
        return []

    # Sort the cells by columns first, and then by rows,
    # since the user typically selects cells by columns.
    cells = sorted(cells, key=lambda p: (p[0], p[1]))

    # Group cells into columns
    column = [cells[0]]
    columns = [column]
    for bottom_most, cell in zip(cells[:-1], cells[1:]):
        if bottom_most[0] == cell[0] and bottom_most[1] == cell[1] - 1:
            # contiguous cell => same column
            column.append(cell)
        else:
            # discontinus cell => new column
            column = [cell]
            columns.append(column)

    # Keep only the top and bottom cells of each column
    columns = [[c[0], c[-1]] for c in columns]

    # Sort the columns by y-axis first and x-axis after
    columns = sorted(columns, key=lambda c: (c[0][1], c[-1][1], c[0][0]))

    # Group columns into slices
    rectangle = [columns[0]]
    rectangles = [rectangle]
    for right_most, column in zip(columns[:-1], columns[1:]):
        if (
            right_most[0][1] == column[0][1]
            and right_most[-1][1] == column[-1][1]
            and right_most[0][0] == column[0][0] - 1
        ):
            # Contiguous column => same slice
            rectangle.append(column)
        else:
            # Discontinuous column => new slice
            rectangle = [column]
            rectangles.append(rectangle)

    # Create the slices by extracting top-left and bottom-right cell coordinates
    return [(r[0][0], r[-1][-1]) for r in rectangles]


class MatrixManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def update_matrix(
        self,
        study: Study,
        path: str,
        edit_instructions: List[MatrixEditInstructionDTO],
    ) -> None:
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        matrix_service = (
            self.storage_service.variant_study_service.command_factory.command_context.matrix_service
        )

        matrix_node = file_study.tree.get_node(url=path.split("/"))

        if not isinstance(matrix_node, InputSeriesMatrix):
            raise TypeError(repr(type(matrix_node)))

        try:
            matrix_df: pd.DataFrame = matrix_node.parse(return_dataframe=True)
        except ValueError as exc:
            raise MatrixManagerError(f"Cannot parse matrix: {exc}") from exc

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
                else:
                    raise MatrixEditError(
                        instr,
                        reason="instruction must contain coordinates or slices",
                    )
            except MatrixUpdateError as exc:
                raise MatrixEditError(instr, reason=str(exc)) from None

        new_matrix_id = matrix_service.create(matrix_df.to_numpy().tolist())

        command = [
            ReplaceMatrix(
                target=path,
                matrix=strip_matrix_protocol(new_matrix_id),
                command_context=self.storage_service.variant_study_service.command_factory.command_context,
            )
        ]

        execute_or_add_commands(
            study=study,
            file_study=file_study,
            commands=command,
            storage_service=self.storage_service,
        )
        if not is_managed(study):
            matrix_node = file_study.tree.get_node(path.split("/"))
            matrix_node.denormalize()
