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
The contract between the agent and a model vendor.

A provider runs one user turn: it sends the conversation to its model, executes the tools the
model asks for through `call_tool`, and loops until the model gives its final answer. Everything
vendor-specific (message format, tool format, reasoning blocks) stays inside the provider.
"""

from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from pydantic import BaseModel, Field


class ToolSpec(BaseModel):
    """A tool the model can call, as described by the MCP server."""

    name: str
    description: str
    input_schema: dict[str, Any]


class ToolOutcome(BaseModel):
    content: str
    is_error: bool = False


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    requests: int = Field(default=0, description="Number of calls to the model API.")


class ChatResult(BaseModel):
    answer: str
    history: list[dict[str, Any]] = Field(
        description=(
            "The conversation after this turn, in the provider's own JSON format. It is opaque for callers: "
            "send it back unchanged with the next message to continue the conversation."
        )
    )
    model: str
    stop_reason: str = Field(description="'end_turn', 'max_tokens', 'refusal' or 'max_tool_rounds'.")
    usage: Usage


ToolCaller = Callable[[str, dict[str, Any]], Awaitable[ToolOutcome]]
TextSink = Callable[[str], Awaitable[None]]


class ProviderError(Exception):
    """An error of the model API, with a message that can be shown to the user."""


class ChatProvider(Protocol):
    name: str
    model: str

    async def run_turn(
        self,
        *,
        system: str,
        history: list[dict[str, Any]],
        user_message: str,
        tools: list[ToolSpec],
        call_tool: ToolCaller,
        on_text: TextSink,
        max_tool_rounds: int,
    ) -> ChatResult:
        """
        Answers `user_message`, calling tools as needed.

        Args:
            system: Instructions for the model.
            history: `ChatResult.history` of the previous turn (empty for a new conversation).
            user_message: The new message of the user.
            tools: The tools the model may call.
            call_tool: Executes a tool; never raises, errors are reported in the outcome.
            on_text: Called with the text the model writes between tool calls (progress notes).
            max_tool_rounds: Maximum number of model calls that request tools.

        Raises:
            ProviderError: if the model API cannot be used (bad key, rate limit, network...).
        """
        ...
