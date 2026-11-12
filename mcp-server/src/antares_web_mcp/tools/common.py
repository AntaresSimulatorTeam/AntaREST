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

"""Building blocks shared by all tool modules."""

from collections.abc import Awaitable
from typing import Annotated, Any

from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from antares_web_mcp.client import AntaresWebError

StudyId = Annotated[
    str,
    Field(
        # Checked here so that a mistyped id fails with a message naming the argument, instead of an
        # anonymous HTTP 422 from Antares Web.
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        description="Study id (UUID), as returned by `list_studies` or `create_study`: copy it exactly.",
    ),
]
AreaId = Annotated[str, Field(description="Area id, as returned by `list_areas` (lower-case normalized name).")]
OutputId = Annotated[str, Field(description="Output id, as returned by `list_outputs` or `get_job`.")]
JobId = Annotated[str, Field(description="Job id, as returned by `launch_study` or `list_jobs`.")]

READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)
ADDITIVE = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False)
UPDATE = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
DESTRUCTIVE = ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=False)

MATRIX_OPERATIONS = {"set": "=", "add": "+", "multiply": "*"}


async def guard[T](awaitable: Awaitable[T]) -> T:
    """
    Converts Antares Web errors into MCP ``ToolError``.

    A ``ToolError`` message is sent back to the model (so it can fix its call, e.g. use the right
    area id), whereas any other exception is reported as an opaque "Error executing tool".
    """
    try:
        return await awaitable
    except AntaresWebError as e:
        raise ToolError(str(e)) from e


def without_none(values: dict[str, Any]) -> dict[str, Any]:
    """Keeps only the provided values: partial updates must not overwrite fields with ``null``."""
    return {key: value for key, value in values.items() if value is not None}


def parse_version(version: str) -> tuple[int, ...]:
    """Parses a study or solver version ('8.8', '10.2' or the legacy '880') into a comparable tuple."""
    if "." in version:
        return tuple(int(part) for part in version.split("."))
    major, minor = (version[:-2], version[-2:-1]) if len(version) >= 3 else (version, "0")
    return int(major), int(minor)
