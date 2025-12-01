# Copyright (c) 2026, RTE (https://www.rte-france.com)
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


class DirectoryNotFoundError(HTTPException):
    """Raised when a directory is not found."""

    def __init__(self, directory_id: str):
        super().__init__(HTTPStatus.NOT_FOUND, f"Directory '{directory_id}' not found")


class DirectoryAlreadyExistsError(HTTPException):
    """Raised when trying to create a directory with a duplicate name."""

    def __init__(self, name: str):
        super().__init__(HTTPStatus.CONFLICT, f"A directory named '{name}' already exists in this location")


class DirectoryCycleError(HTTPException):
    """Raised when moving a directory would create a cycle in the directory tree."""

    def __init__(self) -> None:
        super().__init__(
            HTTPStatus.BAD_REQUEST, "Cannot move directory: this would create a cycle in the directory tree"
        )


class DirectoryNotEmptyError(HTTPException):
    """Raised when trying to delete a non-empty directory without cascade or force options."""

    def __init__(self, message: str):
        super().__init__(HTTPStatus.CONFLICT, message)
