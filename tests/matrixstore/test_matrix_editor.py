# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from typing import Any, Dict

import pytest
from pydantic import ValidationError

from antarest.matrixstore.matrix_editor import OPERATIONS, MatrixEditInstruction, MatrixSlice, Operation


class TestMatrixSlice:
    @pytest.mark.parametrize(
        "kwargs, expected",
        [
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
        ],
    )
    def test_init(self, kwargs: Dict[str, Any], expected: Dict[str, Any]) -> None:
        obj = MatrixSlice(**kwargs)
        assert obj.dict(by_alias=False) == expected


class TestOperation:
    @pytest.mark.parametrize(
        "kwargs, expected",
        [
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
        ],
    )
    def test_init(self, kwargs: Dict[str, Any], expected: Dict[str, Any]) -> None:
        obj = Operation(**kwargs)
        assert obj.dict(by_alias=False) == expected

    @pytest.mark.parametrize("operation", list(OPERATIONS))
    def test_init__valid_operation(self, operation: str) -> None:
        obj = Operation(operation=operation, value=123)
        assert obj.dict(by_alias=False) == {
            "operation": operation,
            "value": 123.0,
        }

    def test_total_ordering(self):
        op1 = Operation(operation="=", value=120)
        op2 = Operation(operation="=", value=150)
        op3 = Operation(operation="/", value=150)
        op4 = Operation(operation="/", value=120)
        operations = [op1, op2, op3, op4]
        operations.sort()
        # note that: "/" < "="
        assert operations == [op4, op3, op1, op2]


class TestMatrixEditInstruction:
    @pytest.mark.parametrize(
        "kwargs, expected",
        [
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
        ],
    )
    def test_init(self, kwargs: Dict[str, Any], expected: Dict[str, Any]) -> None:
        obj = MatrixEditInstruction(**kwargs)
        assert obj.dict(by_alias=False) == expected
