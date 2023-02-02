import operator
from enum import Enum
from typing import Optional, Any, List, cast, Tuple

import numpy as np
import pandas as pd  # type:ignore
from pydantic import BaseModel, validator


class MatrixSlice(BaseModel):
    # row_from <= cells < row_to
    # col_from <= cells < col_to
    row_from: int
    row_to: Optional[int] = None
    column_from: int
    column_to: Optional[int] = None

    @validator("row_to", always=True)
    def set_row_to(cls, v: Optional[int], values: Any) -> int:
        if v is None:
            return cast(int, values["row_from"])
        return v

    @validator("column_to", always=True)
    def set_column_to(cls, v: Optional[int], values: Any) -> int:
        if v is None:
            return cast(int, values["column_from"])
        return v


class Operator(Enum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    ABS = "ABS"
    EQ = "="


class Operation(BaseModel):
    operation: Operator
    value: float

    def compute(self, x: Any, use_coords: bool = False) -> Any:
        def set_series(x):  # type:ignore
            x.loc[~x.isnull()] = self.value
            return x

        operation_dict = {
            Operator.ADD: operator.add,
            Operator.SUB: operator.sub,
            Operator.MUL: operator.mul,
            Operator.DIV: operator.truediv,
            Operator.ABS: lambda x, y: abs(x),
            Operator.EQ: lambda x, y: set_series(x),  # type:ignore
        }
        if not use_coords:
            operation_dict[Operator.EQ] = lambda x, y: set_series(
                x
            )  # type:ignore
        else:
            operation_dict[Operator.EQ] = lambda x, y: y

        return operation_dict[self.operation](x, self.value)  # type: ignore


class MatrixEditInstructionDTO(BaseModel):
    slices: Optional[List[MatrixSlice]] = None
    coordinates: Optional[List[Tuple[int, int]]] = None
    operation: Operation


class MatrixEditor:
    @staticmethod
    def update_matrix_content_with_slices(
        matrix_data: pd.DataFrame,
        slices: List[MatrixSlice],
        operation: Operation,
    ) -> pd.DataFrame:
        mask = pd.DataFrame(np.zeros(matrix_data.shape), dtype=bool)

        for matrix_slice in slices:
            mask.loc[
                matrix_slice.row_from : matrix_slice.row_to,
                matrix_slice.column_from : matrix_slice.column_to,
            ] = True

        new_matrix_data = matrix_data.where(mask).apply(operation.compute)
        new_matrix_data[new_matrix_data.isnull()] = matrix_data

        return new_matrix_data.astype(matrix_data.dtypes)

    @staticmethod
    def update_matrix_content_with_coordinates(
        df: pd.DataFrame,
        coordinates: List[Tuple[int, int]],
        operation: Operation,
    ) -> pd.DataFrame:
        for row, column in coordinates:
            df.iat[row, column] = operation.compute(
                df.iat[row, column], use_coords=True
            )
        return df.astype(df.dtypes)
