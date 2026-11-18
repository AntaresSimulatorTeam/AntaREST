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
Provider for any server speaking the OpenAI chat completions API: a model hosted on your own network
behind a LiteLLM gateway, vLLM, Ollama or llama.cpp, or the API of a vendor.

Plain HTTP calls rather than a vendor SDK: the protocol is one endpoint, and the agent needs its
own trace of the tool calls, a cap on the number of rounds and a JSON-serializable history.
"""

import json
import re
from typing import Any

import httpx2

from antares_web_mcp.assistant.provider import (
    ChatResult,
    ProviderError,
    TextSink,
    ToolCaller,
    ToolOutcome,
    ToolSpec,
    Usage,
)

# A model hosted locally can take minutes to write a long answer.
REQUEST_TIMEOUT = httpx2.Timeout(600.0, connect=15.0)
# Reasoning written inline by some models (Qwen, DeepSeek...) when the server does not give it apart.
REASONING = re.compile(r"<think>.*?</think>\s*", re.DOTALL)
STOP_REASONS = {"length": "max_tokens", "content_filter": "refusal"}


class OpenAICompatibleProvider:
    def __init__(self, client: httpx2.AsyncClient, *, model: str) -> None:
        """
        Args:
            client: HTTP client of the server: its base URL ends with `/v1/`, and it carries the API key, if any.
            model: Id of the model, as listed by `GET <base URL>/models`.
        """
        self._client = client
        self.model = model

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
        messages: list[dict[str, Any]] = [*history, {"role": "user", "content": user_message}]
        tool_params = [
            {
                "type": "function",
                "function": {"name": tool.name, "description": tool.description, "parameters": tool.input_schema},
            }
            for tool in tools
        ]
        usage = Usage()
        model = self.model

        for _ in range(max_tool_rounds + 1):
            # The instructions are not kept in the history: they are sent again with each call.
            response = await self._complete([{"role": "system", "content": system}, *messages], tool_params)
            _add_usage(usage, response)
            model = response.get("model") or model
            choice = response["choices"][0]
            message = choice.get("message") or {}
            answer = REASONING.sub("", message.get("content") or "").strip()
            calls: list[dict[str, Any]] = message.get("tool_calls") or []
            # Only what the model needs to continue goes back in the history: not its reasoning.
            messages.append({"role": "assistant", "content": answer} | ({"tool_calls": calls} if calls else {}))

            if not calls:
                stop_reason = STOP_REASONS.get(choice.get("finish_reason"), "end_turn")
                break
            if answer:
                await on_text(answer)
            for call in calls:
                outcome = await _run(call, call_tool)
                messages.append({"role": "tool", "tool_call_id": call.get("id"), "content": outcome.content})
        else:
            answer = f"Stopped after {max_tool_rounds} rounds of tool calls without a final answer."
            stop_reason = "max_tool_rounds"

        if stop_reason == "max_tokens":
            answer += "\n\n[The answer was cut: it reached the output limit. Ask to continue.]"
        elif stop_reason == "refusal" and not answer:
            answer = "The model declined to answer this request."
        return ChatResult(answer=answer, history=messages, model=model, stop_reason=stop_reason, usage=usage)

    async def _complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        body = {"model": self.model, "messages": messages} | ({"tools": tools} if tools else {})
        try:
            response = await self._client.post("chat/completions", json=body, timeout=REQUEST_TIMEOUT)
        except httpx2.HTTPError as e:
            raise ProviderError(
                f"Cannot reach the model endpoint {self._client.base_url}: {e or type(e).__name__}. "
                "Check the proxy and the certificates of the server."
            ) from e
        if response.status_code == 401:
            raise ProviderError("The model endpoint rejected the API key: check `assistant.api_key`.")
        if response.status_code == 429:
            raise ProviderError(f"The quota or the rate limit of the model endpoint is reached: {_detail(response)}")
        if response.is_error:
            raise ProviderError(
                f"The model endpoint returned an error (HTTP {response.status_code}) "
                f"for the model '{self.model}': {_detail(response)}"
            )
        completion: dict[str, Any] = response.json()
        if not completion.get("choices"):
            raise ProviderError(f"The model endpoint returned no answer: {response.text[:300]}")
        return completion


async def _run(call: dict[str, Any], call_tool: ToolCaller) -> ToolOutcome:
    function = call.get("function") or {}
    try:
        arguments = json.loads(function.get("arguments") or "{}")
    except ValueError:
        arguments = None
    if not isinstance(arguments, dict):
        # A small model can write broken JSON: it gets the error as the result of its call, and can try again.
        return ToolOutcome(
            content="The arguments of this tool call are not a JSON object: write them again.", is_error=True
        )
    return await call_tool(function.get("name", ""), arguments)


def _detail(response: httpx2.Response) -> str:
    """The message of an error, as OpenAI-compatible servers give it: `{"error": {"message": ...}}`."""
    try:
        error = response.json().get("error")
    except (ValueError, AttributeError):
        return response.text[:300]
    return str(error.get("message") if isinstance(error, dict) else error or response.text[:300])


def _add_usage(usage: Usage, completion: dict[str, Any]) -> None:
    counts = completion.get("usage") or {}
    usage.requests += 1
    usage.input_tokens += counts.get("prompt_tokens") or 0
    usage.output_tokens += counts.get("completion_tokens") or 0
    usage.cache_read_input_tokens += (counts.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
