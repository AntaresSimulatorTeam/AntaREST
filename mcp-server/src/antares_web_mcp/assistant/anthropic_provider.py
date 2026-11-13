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
Claude (Anthropic API) provider.

The tool loop is written by hand rather than with the SDK tool runner because the agent needs
its own trace of tool calls, a cap on the number of rounds and a JSON-serializable history.
"""

from typing import Any, Literal, cast

import anthropic
from anthropic.types.beta import BetaMessage, BetaMessageParam, BetaToolUnionParam

from antares_web_mcp.assistant.provider import ChatResult, ProviderError, TextSink, ToolCaller, ToolSpec, Usage

DEFAULT_MODEL = "claude-opus-5-5"
Effort = Literal["low", "medium", "high", "xhigh", "max"]
MAX_TOKENS = 16000  # per model call; higher values require streaming

# Safety classifiers of these models may decline a request: the API then re-runs it on the fallback
# model Anthropic recommends, within the same call. Other models do not accept the parameter.
FALLBACK_BETA = "server-side-fallback-2026-07-01"
MODELS_WITH_FALLBACK = {"claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}


class AnthropicProvider:
    name = "anthropic"

    def __init__(
        self,
        client: anthropic.AsyncAnthropic,
        *,
        model: str = DEFAULT_MODEL,
        effort: Effort = "medium",
    ) -> None:
        self._client = client
        self.model = model
        self.effort: Effort = effort

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
            {"name": tool.name, "description": tool.description, "input_schema": tool.input_schema} for tool in tools
        ]
        usage = Usage()
        answer: list[str] = []
        stop_reason = "max_tool_rounds"
        model = self.model

        for _ in range(max_tool_rounds + 1):
            response = await self._create(system, messages, tool_params)
            _add_usage(usage, response)
            model = response.model
            # The whole content goes back in the history, unchanged: the model needs its reasoning
            # blocks and its tool calls to continue.
            messages.append(
                {"role": "assistant", "content": [block.to_dict(mode="json") for block in response.content]}
            )
            texts = [block.text for block in response.content if block.type == "text" and block.text.strip()]

            if response.stop_reason == "refusal":
                # Checked before reading the content: a refused response has no usable answer.
                details = response.stop_details
                reason = (details.explanation if details else None) or "no explanation given"
                answer = [f"The model declined to answer this request ({reason})."]
                stop_reason = "refusal"
                break
            if response.stop_reason == "pause_turn":
                continue  # the API paused a long turn: sending the conversation again resumes it
            if response.stop_reason != "tool_use":
                answer = texts
                stop_reason = response.stop_reason or "end_turn"
                break

            for text in texts:
                await on_text(text)
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    outcome = await call_tool(block.name, dict(block.input))
                    results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": outcome.content,
                            "is_error": outcome.is_error,
                        }
                    )
            # All the results of a round go in a single user message.
            messages.append({"role": "user", "content": results})
        else:
            answer = [f"Stopped after {max_tool_rounds} rounds of tool calls without a final answer."]

        text = "\n\n".join(answer)
        if stop_reason == "max_tokens":
            text += "\n\n[The answer was cut: it reached the output limit. Ask to continue.]"
        return ChatResult(answer=text, history=messages, model=model, stop_reason=stop_reason, usage=usage)

    async def _create(self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> BetaMessage:
        with_fallback = self.model in MODELS_WITH_FALLBACK
        try:
            return await self._client.beta.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=cast(list[BetaMessageParam], messages),
                tools=cast(list[BetaToolUnionParam], tools),
                output_config={"effort": self.effort},
                # Caches the prefix (tools, system, conversation): each round of the tool loop
                # re-sends everything, and reads it from the cache at a fraction of the price.
                cache_control={"type": "ephemeral"},
                betas=[FALLBACK_BETA] if with_fallback else anthropic.omit,
                fallbacks="default" if with_fallback else anthropic.omit,
            )
        except anthropic.AuthenticationError as e:
            raise ProviderError("The Anthropic API key is invalid or revoked.") from e
        except anthropic.PermissionDeniedError as e:
            raise ProviderError(f"The Anthropic API key cannot use model '{self.model}': {e.message}") from e
        except anthropic.NotFoundError as e:
            raise ProviderError(f"Unknown model '{self.model}': {e.message}") from e
        except anthropic.RateLimitError as e:
            raise ProviderError("The Anthropic API rate limit is reached, retry in a moment.") from e
        except anthropic.APIStatusError as e:
            raise ProviderError(f"The Anthropic API returned an error (HTTP {e.status_code}): {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise ProviderError(f"Cannot reach the Anthropic API: {e}") from e


def _add_usage(usage: Usage, response: BetaMessage) -> None:
    usage.requests += 1
    usage.input_tokens += response.usage.input_tokens
    usage.output_tokens += response.usage.output_tokens
    usage.cache_read_input_tokens += response.usage.cache_read_input_tokens or 0
    usage.cache_creation_input_tokens += response.usage.cache_creation_input_tokens or 0
