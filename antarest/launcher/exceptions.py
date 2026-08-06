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


class InvalidScheduleTime(HTTPException):
    """Raised when a requested scheduled start time is invalid or unsupported (maps to HTTP 400)."""

    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, message)


class NoValidOutputError(Exception):
    """
    Raised when a launch leaves no importable Antares output (e.g. a failed launch that
    only produced a `simulation.log` instead of a proper output directory or ZIP).

    Launcher adapters catch this to mark the job as failed instead of crashing.
    """
