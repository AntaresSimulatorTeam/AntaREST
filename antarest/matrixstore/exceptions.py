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

from http import HTTPStatus

from fastapi import HTTPException


class MatrixDataSetNotFound(HTTPException):
    def __init__(self) -> None:
        super().__init__(HTTPStatus.NOT_FOUND)


class MatrixNotFound(HTTPException):
    def __init__(self, matrix_id: str) -> None:
        message = f"Matrix {matrix_id} doesn't exist"
        super().__init__(HTTPStatus.NOT_FOUND, message)


class MatrixNotSupported(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, f"Could not save the matrix: {message}")
