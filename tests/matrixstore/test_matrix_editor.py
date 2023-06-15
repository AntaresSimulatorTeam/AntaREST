from typing import Dict, Any

import pytest
from pydantic import ValidationError

from antarest.matrixstore.matrix_editor import (
    MatrixSlice,
    Operation,
    MatrixEditInstruction,
    OPERATIONS,
)


class TestMatrixSlice:
    @pytest.mark.parametrize(
        "kwargs, expected",
        [
            # fmt: off
            pytest.param(
                {"column_from": "5", "column_to": "8", "row_from": "0", "row_to": "8760"},
                {"column_from": 5, "column_to": 8, "row_from": 0, "row_to": 8760},
                id="nominal-case-str",
            ),
            pytest.param(
                {"column_from": 5, "column_to": 8, "row_from": 0, "row_to": 8760},
                {"column_from": 5, "column_to": 8, "row_from": 0, "row_to": 8760},
                id="nominal-case-int",
            ),
            pytest.param(
                {"column_from": 5, "row_from": 0, "row_to": 8760},
                {"column_from": 5, "column_to": 5, "row_from": 0, "row_to": 8760},
                id="column_to-missing",
            ),
            pytest.param(
                {"column_from": 5, "column_to": 8, "row_from": 0},
                {"column_from": 5, "column_to": 8, "row_from": 0, "row_to": 0},
                id="row_to-missing",
            ),
            pytest.param(
                {"column_to": 8, "row_from": 0, "row_to": 8760},
                {"column_from": 5, "column_to": 8, "row_from": 0, "row_to": 8760},
                id="column_from-missing-BAD",
                marks=pytest.mark.xfail(reason="field required", raises=ValidationError, strict=True),
            ),
            pytest.param(
                {"column_from": 5, "column_to": 8, "row_to": 8760},
                {"column_from": 5, "column_to": 8, "row_from": 0, "row_to": 8760},
                id="row_from-missing-BAD",
                marks=pytest.mark.xfail(reason="field required", raises=ValidationError, strict=True),
            ),
            pytest.param(
                {"column_from": 5, "column_to": 4, "row_from": 0, "row_to": 8760},
                {"column_from": 5, "column_to": 4, "row_from": 0, "row_to": 8760},
                id="column_to-less-than_column_from-BAD",
                marks=pytest.mark.xfail(reason="invalid range", raises=ValidationError, strict=True),
            ),
            pytest.param(
                {"column_from": 5, "column_to": 8, "row_from": 5, "row_to": 4},
                {"column_from": 5, "column_to": 8, "row_from": 5, "row_to": 4},
                id="row_to-less-row_from-BAD",
                marks=pytest.mark.xfail(reason="invalid range", raises=ValidationError, strict=True),
            ),
            pytest.param(
                {"column_from": -1, "column_to": 8, "row_from": 0, "row_to": 8760},
                {"column_from": -1, "column_to": 8, "row_from": 0, "row_to": 8760},
                id="column_from-is-negative-BAD",
                marks=pytest.mark.xfail(reason="negative value", raises=ValidationError, strict=True),
            ),
            pytest.param(
                {"column_from": 5, "column_to": 8, "row_from": -1, "row_to": 8760},
                {"column_from": 5, "column_to": 8, "row_from": -1, "row_to": 8760},
                id="row_from-is-negative-BAD",
                marks=pytest.mark.xfail(reason="negative value", raises=ValidationError, strict=True),
            ),
            # fmt: on
        ],
    )
    def test_init(
        self, kwargs: Dict[str, Any], expected: Dict[str, Any]
    ) -> None:
        obj = MatrixSlice(**kwargs)
        assert obj.dict(by_alias=False) == expected


class TestOperation:
    @pytest.mark.parametrize(
        "kwargs, expected",
        [
            # fmt: off
            pytest.param(
                {"operation": "=", "value": "120"},
                {"operation": "=", "value": 120.0},
                id="nominal-case-str",
            ),
            pytest.param(
                {"operation": "=", "value": 120.0},
                {"operation": "=", "value": 120.0},
                id="nominal-case-float",
            ),
            pytest.param(
                {"operation": "%", "value": 120.0},
                {"operation": "%", "value": 120.0},
                id="operation-unknown",
                marks=pytest.mark.xfail(reason="unknown operation", raises=ValidationError, strict=True),
            ),
            # fmt: on
        ],
    )
    def test_init(
        self, kwargs: Dict[str, Any], expected: Dict[str, Any]
    ) -> None:
        obj = Operation(**kwargs)
        assert obj.dict(by_alias=False) == expected

    @pytest.mark.parametrize("operation", list(OPERATIONS))
    def test_init__valid_operation(self, operation: str) -> None:
        obj = Operation(operation=operation, value=123)
        assert obj.dict(by_alias=False) == {
            "operation": operation,
            "value": 123.0,
        }


class TestMatrixEditInstruction:
    @pytest.mark.parametrize(
        "kwargs, expected",
        [
            # fmt: off
            pytest.param(
                {
                    "operation": {"operation": "=", "value": 120.0},
                    "slices": [
                        {"column_from": 1, "column_to": 2, "row_from": 0, "row_to": 8760},
                        {"column_from": 3, "column_to": 5, "row_from": 0, "row_to": 8760},
                    ],
                },
                {
                    "coordinates": None,
                    "operation": {"operation": "=", "value": 120.0},
                    "slices": [
                        {"column_from": 1, "column_to": 2, "row_from": 0, "row_to": 8760},
                        {"column_from": 3, "column_to": 5, "row_from": 0, "row_to": 8760},
                    ],
                },
                id="nominal-case-slices",
            ),
            pytest.param(
                {
                    "coordinates": [(0, 0), (0, 1), (5, 8)],
                    "operation": {"operation": "=", "value": 120.0},
                },
                {
                    "coordinates": [(0, 0), (0, 1), (5, 8)],
                    "operation": {"operation": "=", "value": 120.0},
                    "slices": None,
                },
                id="nominal-case-coordinates",
            ),
            pytest.param(
                {
                    "operation": {"operation": "=", "value": 120.0},
                },
                {},
                id="slices-and-coordinates-missing-BAD",
                marks=pytest.mark.xfail(reason="none defined", raises=ValidationError, strict=True),
            ),
            pytest.param(
                {
                    "coordinates": [(1, 2)],
                    "operation": {"operation": "=", "value": 120.0},
                    "slices": [{"column_from": 1, "column_to": 2, "row_from": 0, "row_to": 8760}],
                },
                {},
                id="slices-and-coordinates-both-defined-BAD",
                marks=pytest.mark.xfail(reason="both defined", raises=ValidationError, strict=True),
            ),
            pytest.param(
                {
                    "coordinates": [(-1, 2)],
                    "operation": {"operation": "=", "value": 120.0},
                },
                {},
                id="coordinates-negative-col-BAD",
                marks=pytest.mark.xfail(reason="negative value", raises=ValidationError, strict=True),
            ),
            pytest.param(
                {
                    "coordinates": [(1, -1)],
                    "operation": {"operation": "=", "value": 120.0},
                },
                {},
                id="coordinates-negative-row-BAD",
                marks=pytest.mark.xfail(reason="negative value", raises=ValidationError, strict=True),
            ),
            # fmt: on
        ],
    )
    def test_init(
        self, kwargs: Dict[str, Any], expected: Dict[str, Any]
    ) -> None:
        obj = MatrixEditInstruction(**kwargs)
        assert obj.dict(by_alias=False) == expected
