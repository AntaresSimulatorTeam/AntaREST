import operator
from enum import Enum
from typing import Optional, Any, List, cast

import xarray as xr
from pydantic import BaseModel, validator

from antarest.matrixstore.model import MatrixData


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
            return cast(int, values["row_from"] + 1)
        return v

    @validator("column_to", always=True)
    def set_column_to(cls, v: Optional[int], values: Any) -> int:
        if v is None:
            return cast(int, values["column_from"] + 1)
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

    def compute(self, x: Any) -> Any:
        operation_dict = {
            Operator.ADD: operator.add,
            Operator.SUB: operator.sub,
            Operator.MUL: operator.mul,
            Operator.DIV: operator.truediv,
            Operator.ABS: lambda x, y: abs(x),
            Operator.EQ: lambda x, y: y,
        }
        return operation_dict[self.operation](x, self.value)  # type: ignore


class MatrixEditInstructionDTO(BaseModel):
    slices: List[MatrixSlice]
    operation: Operation


class MatrixEditor:
    @staticmethod
    def update_matrix_content_with_slices(
        matrix_data: List[List[MatrixData]],
        slices: List[MatrixSlice],
        operation: Operation,
    ) -> List[List[MatrixData]]:

        data_array = xr.DataArray(matrix_data, dims=["row", "col"])

        mask = xr.zeros_like(data_array, dtype=bool)
        for matrix_slice in slices:
            mask |= (
                (data_array.coords["row"] >= matrix_slice.row_from)
                & (data_array.coords["row"] < matrix_slice.row_to)
                & (data_array.coords["col"] >= matrix_slice.column_from)
                & (data_array.coords["col"] < matrix_slice.column_to)
            )

        new_matrix_data = xr.where(
            mask,
            operation.compute(data_array),  # type:ignore
            data_array,
        ).data.tolist()
        return new_matrix_data  # type:ignore
