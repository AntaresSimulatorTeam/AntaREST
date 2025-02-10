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

import functools
import operator
from typing import Any, Dict, List, Optional, Tuple

from pydantic import Field, field_validator, model_validator
from typing_extensions import override

from antarest.core.serde import AntaresBaseModel


class MatrixSlice(AntaresBaseModel):
    # NOTE: This Markdown documentation is reflected in the Swagger API
    """
    Represents a group of cells in a matrix for updating.

    Attributes:
    - `column_from`: Starting column index (inclusive) for the slice.
    - `column_to`: Ending column index (inclusive) for the slice. Defaults to `column_from`.
    - `row_from`: Starting row index (inclusive) for the slice.
    - `row_to`: Ending row index (inclusive) for the slice. Defaults to `row_from`.
    """

    row_from: int
    row_to: int
    column_from: int
    column_to: int

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "column_from": 5,
                "column_to": 8,
                "row_from": 0,
                "row_to": 8760,
            }
        }

    @model_validator(mode="before")
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
                    f"Invalid row range: {row_from}..{row_to}. 'row_from' must be less than or equal to 'row_to'."
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


@functools.total_ordering
class Operation(AntaresBaseModel):
    # NOTE: This Markdown documentation is reflected in the Swagger API
    """
    Represents an update operation to be performed on matrix cells.

    Attributes:
     - `operation`: The operation symbol: "+", "-", "*", "/", "ABS" or "=".
     - `value`: The value associated with the operation.
    """

    operation: str = Field(pattern=r"[=/*+-]|ABS")
    value: float

    class Config:
        extra = "forbid"
        json_schema_extra = {"example": {"operation": "=", "value": 120.0}}

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

    @override
    def __str__(self) -> str:
        """Returns a string representation used in error messages."""
        return f"['{self.operation}' {self.value}]"

    def __le__(self, other: Any) -> bool:
        """
        Compares two operations (used for sorting and grouping).
        """
        if isinstance(other, Operation):
            # noinspection PyTypeChecker
            return (self.operation, self.value).__le__((other.operation, other.value))
        return NotImplemented  # pragma: no cover


class MatrixEditInstruction(AntaresBaseModel):
    # NOTE: This Markdown documentation is reflected in the Swagger API
    """
    Provides edit instructions to be applied to a matrix.

    Attributes:
    - `slices`: The matrix slices to edit.
    - `coordinates`: The coordinates of the matrix cells to edit.
    - `operation`: The update operation (simple assignment or mathematical operator)
      to perform on the matrix.
    """

    slices: Optional[List[MatrixSlice]] = None
    coordinates: Optional[List[Tuple[int, int]]] = None
    operation: Operation

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "column_from": 5,
                "column_to": 8,
                "row_from": 0,
                "row_to": 8760,
            }
        }

    @model_validator(mode="before")
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

        if slices is None and coordinates is None:
            raise ValueError("At least 'slices' or 'coordinates' must be defined.")
        if slices is not None and coordinates is not None:
            raise ValueError("Only 'slices' or 'coordinates' could be defined, but not both.")

        return values

    @field_validator("coordinates")
    def validate_coordinates(cls, coordinates: Optional[List[Tuple[int, int]]]) -> Optional[List[Tuple[int, int]]]:
        """
        Validates the `coordinates` field.

        Args:
           coordinates: The coordinates to validate.

        Returns:
           The validated coordinates.

        Raises:
           ValueError: If any coordinate value is less than 0.
        """
        if coordinates is None:  # pragma: no cover
            return None
        for coordinate in coordinates:
            if coordinate[0] < 0 or coordinate[1] < 0:
                raise ValueError(f"Invalid coordinate {coordinate}:  values must be greater than or equal to 0.")
        return coordinates

    @override
    def __str__(self) -> str:
        """Returns a string representation used in error messages."""

        if self.slices:
            return f"slices={self.slices}, operation={self.operation}"
        elif self.coordinates:
            return f"coordinates={self.coordinates}, operation={self.operation}"

        raise NotImplementedError
