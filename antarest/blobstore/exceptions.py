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


class BlobNotFound(HTTPException):
    def __init__(self, blob_id: str) -> None:
        message = f"Blob {blob_id} doesn't exist"
        super().__init__(HTTPStatus.NOT_FOUND, message)
