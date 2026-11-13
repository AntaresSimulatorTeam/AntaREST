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

"""
The agent: connects a model provider to the MCP tools for one user turn.

The tools come from the same MCP server as the one used by Claude Code or GitHub Copilot, through
an in-memory MCP client: the assistant and the IDE assistants share one definition of the tools.
"""

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, Literal

from mcp import Client
from mcp.types import TextContent
from pydantic import BaseModel, Field

from antares_web_mcp.assistant.provider import ChatProvider, ChatResult, ToolOutcome, ToolSpec
from antares_web_mcp.client import AntaresWebClient
from antares_web_mcp.server import INSTRUCTIONS, create_server

logger = logging.getLogger(__name__)

# A tool result larger than this is cut (with a notice for the model): one huge table must not
# fill the context window of the model.
MAX_TOOL_RESULT_CHARS = 80_000

SYSTEM_PROMPT = """\
You are the assistant of Antares Web, a platform to manage Antares Simulator studies (power system
adequacy and economic simulations). You help study engineers understand, check and analyse their
studies.

You work with tools that act on the Antares Web server the user is connected to, with the user's
own permissions.

{instructions}
How to answer:
- Base every statement about a study on tool results obtained in this conversation. Never give a
  figure you have not read. If a tool fails or some data is missing, say so.
- Give figures with their units (MW, GWh, EUR/MWh) and name the objects (area, cluster, link and
  constraint ids), so that the user can find them in Antares Web.
- Separate what you read in the study from what you infer. A surprising value is often a
  deliberate modelling choice: present it as a point to confirm with the author of the study,
  and as an error only when it is certain.
- Answer in the language of the user. Lead with the answer and keep it as short as the question
  allows. Use Markdown, with a short table when you compare values.
- {mode}
"""
READ_ONLY_MODE = (
    "This session is read-only: you cannot modify studies or launch simulations. When the user asks "
    "for a change, explain what to change and where."
)
READ_WRITE_MODE = (
    "You can modify studies and launch simulations. Ask for confirmation before any modification "
    "the user did not explicitly request, and before any deletion."
)


class AssistantRequest(BaseModel):
    """One user turn, as sent by the Antares Web backend."""

    message: str = Field(min_length=1)
    history: list[dict[str, Any]] = Field(default_factory=list, description="`history` of the previous answer.")
    study_id: str | None = Field(default=None, description="Study the user is working on, if any.")
    antares_url: str = "http://localhost:8080"
    token: str | None = Field(default=None, description="Token of the user: tools act with their permissions.")
    read_only: bool = True
    provider: str = "anthropic"
    model: str | None = None
    effort: Literal["low", "medium", "high", "xhigh", "max"] = "medium"
    max_tool_rounds: int = Field(default=40, ge=1, le=200)
    verify_ssl: bool = True


Emit = Callable[[dict[str, Any]], Awaitable[None]]
"""Receives the events of a turn: `tool_call`, `tool_progress`, `tool_result` and `text` (progress notes)."""


def build_system_prompt(read_only: bool) -> str:
    return SYSTEM_PROMPT.format(instructions=INSTRUCTIONS, mode=READ_ONLY_MODE if read_only else READ_WRITE_MODE)


def build_user_message(request: AssistantRequest) -> str:
    if not request.study_id:
        return request.message
    return f"[The user is currently working on the study with id {request.study_id}.]\n\n{request.message}"


def tool_text(content: list[Any]) -> str:
    text = "\n".join(block.text for block in content if isinstance(block, TextContent))
    if len(text) > MAX_TOOL_RESULT_CHARS:
        text = (
            text[:MAX_TOOL_RESULT_CHARS]
            + f"\n[Result cut: {len(text)} characters, only the first {MAX_TOOL_RESULT_CHARS} are shown. "
            "Narrow the request (filters, fewer columns or rows) to get the rest.]"
        )
    return text


async def run_assistant(
    request: AssistantRequest,
    provider: ChatProvider,
    emit: Emit,
    *,
    antares_client: AntaresWebClient | None = None,
) -> ChatResult:
    """
    Answers one user message with `provider`, giving it the MCP tools of Antares Web.

    Args:
        request: The user turn.
        provider: The model provider.
        emit: Receives the events of the turn as they happen.
        antares_client: Client of the Antares Web REST API (built from the request by default).
            It is closed when the turn ends.
    """
    client = antares_client or AntaresWebClient(
        request.antares_url, token=request.token, timeout=120.0, verify_ssl=request.verify_ssl
    )
    server = create_server(client, read_only=request.read_only)
    async with Client(server) as mcp:
        tools = [
            ToolSpec(name=tool.name, description=tool.description or "", input_schema=tool.input_schema)
            for tool in (await mcp.list_tools()).tools
        ]

        async def call_tool(name: str, arguments: dict[str, Any]) -> ToolOutcome:
            await emit({"type": "tool_call", "name": name, "input": arguments})

            async def on_progress(progress: float, total: float | None, message: str | None) -> None:
                # Long tools (`check_study`, `wait_for_job`) report their progress: user interfaces show it.
                await emit(
                    {"type": "tool_progress", "name": name, "progress": progress, "total": total, "message": message}
                )

            start = time.monotonic()
            try:
                result = await mcp.call_tool(name, arguments, progress_callback=on_progress)
                outcome = ToolOutcome(content=tool_text(result.content), is_error=bool(result.is_error))
            except Exception as e:
                # Whatever goes wrong in a tool, the model must get an answer to its call: it can
                # then fix its arguments, try another tool or report the failure to the user.
                logger.warning(f"Tool {name} failed", exc_info=e)
                outcome = ToolOutcome(content=f"The tool call failed: {e}", is_error=True)
            duration = round(time.monotonic() - start, 2)
            await emit(
                {
                    "type": "tool_result",
                    "name": name,
                    "is_error": outcome.is_error,
                    "duration_s": duration,
                    # What the model received: lets a user interface show structured results (e.g. findings).
                    "content": outcome.content,
                }
            )
            return outcome

        async def on_text(text: str) -> None:
            await emit({"type": "text", "text": text})

        return await provider.run_turn(
            system=build_system_prompt(request.read_only),
            history=request.history,
            user_message=build_user_message(request),
            tools=tools,
            call_tool=call_tool,
            on_text=on_text,
            max_tool_rounds=request.max_tool_rounds,
        )
