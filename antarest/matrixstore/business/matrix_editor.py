import operator
from typing import Any, List, Optional, Tuple, Dict

from pydantic import BaseModel, validator, Field, root_validator


class MatrixSlice(BaseModel):
    # row_from <= cells < row_to
    # col_from <= cells < col_to
    row_from: int
    row_to: Optional[int] = None
    column_from: int
    column_to: Optional[int] = None

    @validator("row_to", always=True)
    def set_row_to(cls, v: Optional[int], values: Any) -> int:
        return values["row_from"] if v is None else v  # type: ignore

    @validator("column_to", always=True)
    def set_column_to(cls, v: Optional[int], values: Any) -> int:
        return values["column_from"] if v is None else v  # type: ignore


OPERATIONS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "ABS": lambda x, y: abs(x),
    "=": lambda x, y: y,
}


class Operation(BaseModel):
    operation: str = Field(regex=r"[=/*+-]|ABS")
    value: float

    # noinspection SpellCheckingInspection
    def compute(self, x: Any, use_coords: bool = False) -> Any:
        if use_coords:
            return OPERATIONS[self.operation](x, self.value)  # type: ignore
        if self.operation == "=":
            x.loc[~x.isnull()] = self.value
            return x
        return OPERATIONS[self.operation](x, self.value)  # type: ignore

    def __str__(self) -> str:
        return f"['{self.operation}' {self.value}]"


class MatrixEditInstructionDTO(BaseModel):
    slices: Optional[List[MatrixSlice]] = None
    coordinates: Optional[List[Tuple[int, int]]] = None
    operation: Operation

    @root_validator(pre=True)
    def check_slice_coordinates(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates the 'slices' and 'coordinates' fields.

        Args:
            values: The input values for validation.

        Returns:
            The validated values.

        Raises:
            ValueError: If both 'slices' and 'coordinates' are `None`.
            ValueError: If both 'slices' and 'coordinates' are both defined.
        """
        slices = values.get("slices")
        coordinates = values.get("coordinates")
        # fmt: off
        if slices is None and coordinates is None:
            raise ValueError("At least 'slices' or 'coordinates' must be defined.")
        if slices is not None and coordinates is not None:
            raise ValueError("Only 'slices' or 'coordinates' could be defined, but not both.")
        # fmt: on
        return values

    def __str__(self) -> str:
        # fmt: off
        if self.slices:
            return f"slices={self.slices}, operation={self.operation}"
        elif self.coordinates:
            return f"coordinates={self.coordinates}, operation={self.operation}"
        # fmt: on
        raise NotImplementedError
