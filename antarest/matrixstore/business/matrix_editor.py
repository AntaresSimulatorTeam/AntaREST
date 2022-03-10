import operator
from typing import Optional, Any, Callable, List

import xarray as xr
from pydantic import BaseModel, validator

from antarest.matrixstore.model import MatrixData


class MatrixSlice(BaseModel):
    # row_from <= cells <= row_to
    # col_from <= cells <= col_to
    row_from: int
    row_to: Optional[int] = None
    column_from: int
    column_to: Optional[int] = None

    @validator("row_to", always=True)
    def set_row_to(cls, v: Optional[int], values: Any) -> int:
        if v is None:
            return values["row_from"]
        return v

    @validator("column_to", always=True)
    def set_column_to(cls, v: Optional[int], values: Any) -> int:
        if v is None:
            return values["column_from"]
        return v


class Operation(BaseModel):
    operation: str
    value: float


class MatrixEditor:
    @staticmethod
    def _operation_to_operator(operation: str) -> Callable:
        operation_dict = {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "/": operator.truediv,
            "=": lambda x, y: y,
            "ABS": abs,
        }
        return operation_dict[operation]

    @classmethod
    def update_matrix_content_with_slices(
        cls,
        matrix_data: List[List[MatrixData]],
        slices: List[MatrixSlice],
        operation: Operation,
    ) -> List[List[MatrixData]]:

        data_array = xr.DataArray(matrix_data, dims=["row", "col"])

        mask = xr.zeros_like(data_array, dtype=bool)
        for matrix_slice in slices:
            mask |= (
                (data_array.coords["row"] >= matrix_slice.row_from)
                & (data_array.coords["row"] <= matrix_slice.row_to)
                & (data_array.coords["col"] >= matrix_slice.column_from)
                & (data_array.coords["col"] <= matrix_slice.column_to)
            )

        operator_func = cls._operation_to_operator(operation.operation)

        new_matrix_data = xr.where(
            mask,
            operator_func(data_array, operation.value),
            data_array,
        ).data.tolist()
        return new_matrix_data
