import operator
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, root_validator, validator


class MatrixSlice(BaseModel):
    """
    Represents a group of cells in a matrix for updating.

    Attributes:
        column_from: Starting column index (inclusive) for the slice.
        column_to: Ending column index (exclusive) for the slice. Defaults to `column_from`.
        row_from: Starting row index (inclusive) for the slice.
        row_to: Ending row index (exclusive) for the slice. Defaults to `row_from`.
    """

    row_from: int
    row_to: int
    column_from: int
    column_to: int

    class Config:
        schema_extra = {
            "example": {
                "column_from": 5,
                "column_to": 8,
                "row_from": 0,
                "row_to": 8760,
            }
        }

    @root_validator(pre=True)
    def check_values(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts and validates the slice coordinates.

        This function handle all the necessary conversions and validations
        in a single pass, to improve efficiency.

        Args:
            values: Dictionary containing the values to be validated.

        Returns:
            The validated and updated dictionary of values.

        Raises:
            ValueError: If any of the values are invalid or if the ranges are incorrect.
        """
        if "column_from" in values:
            col_from = values["column_from"] = int(values["column_from"])
            if "column_to" in values:
                col_to = values["column_to"] = int(values["column_to"])
            else:
                col_to = values["column_to"] = values["column_from"]
            if not (0 <= col_from <= col_to):
                raise ValueError(
                    f"Invalid column range: {col_from}..{col_to}."
                    f" 'column_from' must be less than or equal to 'column_to'."
                )
        if "row_from" in values:
            row_from = values["row_from"] = int(values["row_from"])
            if "row_to" in values:
                row_to = values["row_to"] = int(values["row_to"])
            else:
                row_to = values["row_to"] = values["row_from"]
            if not (0 <= row_from <= row_to):
                raise ValueError(
                    f"Invalid row range: {row_from}..{row_to}."
                    f" 'row_from' must be less than or equal to 'row_to'."
                )
        return values


OPERATIONS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "ABS": lambda x, y: abs(x),
    "=": lambda x, y: y,
}


class Operation(BaseModel):
    """
    Represents an operation to be performed on a value or a matrix.

    Attributes:
        operation: The operation symbol (or function name).
        value: The value associated with the operation.
    """

    operation: str = Field(regex=r"[=/*+-]|ABS")
    value: float

    class Config:
        schema_extra = {"example": {"operation": "=", "value": "120"}}

    # noinspection SpellCheckingInspection
    def compute(self, x: Any, use_coords: bool = False) -> Any:
        """
        Computes the operation on the given value or matrix.
        """
        if use_coords:
            return OPERATIONS[self.operation](x, self.value)  # type: ignore
        if self.operation == "=":
            x.loc[~x.isnull()] = self.value
            return x
        return OPERATIONS[self.operation](x, self.value)  # type: ignore

    def __str__(self) -> str:
        """Returns a string representation used in error messages."""
        return f"['{self.operation}' {self.value}]"


class MatrixEditInstructionDTO(BaseModel):
    """
    Represents a data transfer object for matrix edit instructions.

    Attributes:
        slices: The matrix slices to edit.
        coordinates: The coordinates of the matrix elements to edit.
        operation: The operation to perform on the matrix.
    """

    slices: Optional[List[MatrixSlice]] = None
    coordinates: Optional[List[Tuple[int, int]]] = None
    operation: Operation

    class Config:
        schema_extra = {
            "example": {
                "coordinates": [(1, 2)],
                "operation": {"operation": "=", "value": 120.0},
            }
        }

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

    @validator("coordinates")
    def validate_coordinates(
        cls, coordinates: Optional[List[Tuple[int, int]]]
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Validates the `coordinates` field.

        Args:
           coordinates: The coordinates to validate.

        Returns:
           The validated coordinates.

        Raises:
           ValueError: If any coordinate value is less than 0.
        """
        if coordinates is None:
            return None
        for coordinate in coordinates:
            if coordinate[0] < 0 or coordinate[1] < 0:
                raise ValueError(
                    f"Invalid coordinate {coordinate}: "
                    f" values must be greater than or equal to 0."
                )
        return coordinates

    def __str__(self) -> str:
        """Returns a string representation used in error messages."""
        # fmt: off
        if self.slices:
            return f"slices={self.slices}, operation={self.operation}"
        elif self.coordinates:
            return f"coordinates={self.coordinates}, operation={self.operation}"
        # fmt: on
        raise NotImplementedError
