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

"""Helpers to call the MCP server through a real in-process MCP client, as Claude or Copilot would."""

from typing import Any

from mcp import Client
from mcp.types import CallToolResult, TextContent

from antares_web_mcp.client import AntaresWebClient
from antares_web_mcp.server import create_server

STUDY_ID = "21cdcee2-fd4a-45ca-9305-46fc89959553"


async def call(
    api_client: AntaresWebClient, tool: str, arguments: dict[str, Any], **server_options: Any
) -> CallToolResult:
    async with Client(create_server(api_client, **server_options)) as client:
        return await client.call_tool(tool, arguments)


def error_text(result: CallToolResult) -> str:
    assert result.is_error, result
    content = result.content[0]
    assert isinstance(content, TextContent)
    return content.text


def data(result: CallToolResult) -> Any:
    """Structured result of a successful call (lists and scalars are wrapped in ``{"result": ...}``)."""
    assert not result.is_error, result.content
    content = result.structured_content
    assert content is not None
    return content["result"] if set(content) == {"result"} else content
