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
Tests of the assistant. The model API and Antares Web are both replaced by in-memory HTTP
transports: the real SDKs build the requests and parse the responses, nothing leaves the process.
"""

import io
import json
from typing import Any

import anthropic
import httpx2
import pytest

from antares_web_mcp.assistant.agent import (
    MAX_TOOL_RESULT_CHARS,
    AssistantRequest,
    build_system_prompt,
    run_assistant,
    tool_text,
)
from antares_web_mcp.assistant.anthropic_provider import AnthropicProvider
from antares_web_mcp.assistant.cli import AssistantClient, AssistantClientError, describe_tool_call
from antares_web_mcp.assistant.provider import (
    ChatResult,
    ProviderError,
    TextSink,
    ToolCaller,
    ToolOutcome,
    ToolSpec,
    Usage,
)
from antares_web_mcp.assistant.runner import handle
from antares_web_mcp.client import AntaresWebClient
from tests.fake_antares_web import FakeAntaresWeb
from tests.helpers import STUDY_ID

pytestmark = pytest.mark.anyio

TOOLS = [ToolSpec(name="list_studies", description="Find studies.", input_schema={"type": "object", "properties": {}})]


def model_response(content: list[dict[str, Any]], stop_reason: str, **extra: Any) -> dict[str, Any]:
    return {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "model": "claude-opus-5-5",
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 100, "output_tokens": 20, "cache_read_input_tokens": 50},
    } | extra


class FakeModelApi:
    """Stands for the Anthropic API: returns the scripted responses in order and records the requests."""

    def __init__(self, *responses: httpx2.Response) -> None:
        self.responses = list(responses)
        self.requests: list[httpx2.Request] = []

    def handler(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        return self.responses.pop(0)

    def bodies(self) -> list[dict[str, Any]]:
        return [json.loads(request.content) for request in self.requests]

    def provider(self, model: str = "claude-opus-5-5") -> AnthropicProvider:
        client = anthropic.AsyncAnthropic(
            api_key="test-key",
            base_url="http://anthropic.test",
            max_retries=0,
            http_client=anthropic.DefaultAsyncHttpxClient(transport=httpx2.MockTransport(self.handler)),
        )
        return AnthropicProvider(client, model=model, effort="low")


async def run_turn(provider: AnthropicProvider, **overrides: Any) -> tuple[ChatResult, list[Any]]:
    seen: list[Any] = []

    async def call_tool(name: str, arguments: dict[str, Any]) -> ToolOutcome:
        seen.append((name, arguments))
        return ToolOutcome(content='[{"name": "Base case"}]')

    async def on_text(text: str) -> None:
        seen.append(text)

    arguments: dict[str, Any] = {
        "system": "You are a test.",
        "history": [],
        "user_message": "Which studies do I have?",
        "tools": TOOLS,
        "call_tool": call_tool,
        "on_text": on_text,
        "max_tool_rounds": 5,
    } | overrides
    return await provider.run_turn(**arguments), seen


# ----------------------------------------------------------------------
# Anthropic provider
# ----------------------------------------------------------------------


async def test_anthropic_provider_runs_the_tool_loop() -> None:
    tool_use = {"type": "tool_use", "id": "toolu_1", "name": "list_studies", "input": {"name": "Base"}}
    api = FakeModelApi(
        httpx2.Response(200, json=model_response([{"type": "text", "text": "Let me look."}, tool_use], "tool_use")),
        httpx2.Response(200, json=model_response([{"type": "text", "text": "You have 1 study."}], "end_turn")),
    )

    result, seen = await run_turn(api.provider())

    assert result.answer == "You have 1 study."
    assert result.stop_reason == "end_turn"
    assert seen == ["Let me look.", ("list_studies", {"name": "Base"})]
    assert result.usage == Usage(input_tokens=200, output_tokens=40, cache_read_input_tokens=100, requests=2)

    first, second = api.bodies()
    assert first["model"] == "claude-opus-5-5"
    assert first["system"] == "You are a test."
    assert first["tools"] == [TOOLS[0].model_dump()]
    assert first["output_config"] == {"effort": "low"}
    assert first["cache_control"] == {"type": "ephemeral"}
    assert first["fallbacks"] == "default"
    assert "server-side-fallback-2026-07-01" in api.requests[0].headers["anthropic-beta"]
    assert "thinking" not in first  # always on for this model: the parameter is left to the API default
    # The second request carries the whole first answer and the result of its tool call.
    assert [message["role"] for message in second["messages"]] == ["user", "assistant", "user"]
    assert second["messages"][1]["content"][1] == tool_use
    assert second["messages"][2]["content"] == [
        {"type": "tool_result", "tool_use_id": "toolu_1", "content": '[{"name": "Base case"}]', "is_error": False}
    ]
    # The history is plain JSON: it goes through the Antares Web endpoint and comes back as is.
    assert json.loads(json.dumps(result.history)) == result.history
    assert len(result.history) == 4


async def test_anthropic_provider_continues_a_conversation() -> None:
    api = FakeModelApi(httpx2.Response(200, json=model_response([{"type": "text", "text": "Yes."}], "end_turn")))
    history = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": [{"type": "text", "text": "Hi"}]}]

    result, _ = await run_turn(api.provider(), history=history, user_message="Still there?")

    assert api.bodies()[0]["messages"] == [*history, {"role": "user", "content": "Still there?"}]
    assert len(result.history) == 4


async def test_anthropic_provider_reports_a_refusal() -> None:
    refusal = model_response(
        [], "refusal", stop_details={"type": "refusal", "category": "cyber", "explanation": "Not allowed."}
    )
    api = FakeModelApi(httpx2.Response(200, json=refusal))

    result, _ = await run_turn(api.provider())

    assert result.stop_reason == "refusal"
    assert result.answer == "The model declined to answer this request (Not allowed.)."


async def test_anthropic_provider_stops_after_max_tool_rounds() -> None:
    tool_use = {"type": "tool_use", "id": "toolu_1", "name": "list_studies", "input": {}}
    api = FakeModelApi(*(httpx2.Response(200, json=model_response([tool_use], "tool_use")) for _ in range(3)))

    result, seen = await run_turn(api.provider(), max_tool_rounds=2)

    assert result.stop_reason == "max_tool_rounds"
    assert "Stopped after 2 rounds" in result.answer
    assert len(seen) == 3


async def test_anthropic_provider_without_fallback_for_other_models() -> None:
    api = FakeModelApi(httpx2.Response(200, json=model_response([{"type": "text", "text": "ok"}], "end_turn")))

    await run_turn(api.provider(model="claude-haiku-5-5"))

    assert "fallbacks" not in api.bodies()[0]
    assert "anthropic-beta" not in api.requests[0].headers


@pytest.mark.parametrize(
    "status, expected",
    [(401, "API key is invalid"), (404, "Unknown model"), (429, "rate limit"), (500, "HTTP 500")],
)
async def test_anthropic_provider_errors(status: int, expected: str) -> None:
    error = {"type": "error", "error": {"type": "some_error", "message": "details"}}
    api = FakeModelApi(httpx2.Response(status, json=error))

    with pytest.raises(ProviderError, match=expected):
        await run_turn(api.provider())


# ----------------------------------------------------------------------
# Agent: provider + MCP tools
# ----------------------------------------------------------------------


class ScriptedProvider:
    """A provider that calls the given tools, then answers with their results."""

    name = "scripted"
    model = "scripted-1"

    def __init__(self, *calls: tuple[str, dict[str, Any]]) -> None:
        self.calls = calls
        self.received: dict[str, Any] = {}

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
        self.received = {"system": system, "user_message": user_message, "tools": [tool.name for tool in tools]}
        await on_text("Looking at the studies.")
        outcomes = [await call_tool(name, arguments) for name, arguments in self.calls]
        answer = "\n".join(("ERROR: " if outcome.is_error else "") + outcome.content for outcome in outcomes)
        return ChatResult(
            answer=answer,
            history=[*history, {"q": user_message}],
            model=self.model,
            stop_reason="end_turn",
            usage=Usage(),
        )


async def collect(request: AssistantRequest, provider: ScriptedProvider, api_client: AntaresWebClient) -> Any:
    events: list[dict[str, Any]] = []

    async def emit(event: dict[str, Any]) -> None:
        events.append(event)

    result = await run_assistant(request, provider, emit, antares_client=api_client)
    return result, events


async def test_agent_gives_the_mcp_tools_to_the_provider(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient
) -> None:
    study = {
        "id": STUDY_ID,
        "name": "Base case",
        "version": "9.2",
        "type": "rawstudy",
        "workspace": "default",
        "managed": True,
        "archived": False,
        "updated": "2026-11-13",
    }
    fake_api.route("GET", "/v1/studies", json_body={STUDY_ID: study})
    provider = ScriptedProvider(("list_studies", {}), ("get_study", {"study_id": "not-a-study"}))
    request = AssistantRequest(message="Which studies do I have?", study_id=STUDY_ID)

    result, events = await collect(request, provider, api_client)

    assert "Base case" in result.answer
    assert "ERROR: " in result.answer  # the failed call is reported to the model, not raised
    assert [event["type"] for event in events] == ["text", "tool_call", "tool_result", "tool_call", "tool_result"]
    assert events[1] == {"type": "tool_call", "name": "list_studies", "input": {}}
    assert (events[2]["is_error"], events[4]["is_error"]) == (False, True)
    assert provider.received["user_message"].startswith(
        f"[The user is currently working on the study with id {STUDY_ID}.]"
    )
    # Read-only by default: no tool that modifies a study or launches a simulation.
    assert "check_study" in provider.received["tools"]
    assert not {"create_study", "launch_study", "delete_area"} & set(provider.received["tools"])
    assert "This session is read-only" in provider.received["system"]


async def test_agent_in_read_write_mode(api_client: AntaresWebClient) -> None:
    provider = ScriptedProvider()

    await collect(AssistantRequest(message="Create a study", read_only=False), provider, api_client)

    assert "create_study" in provider.received["tools"]
    assert "Ask for confirmation" in provider.received["system"]
    assert provider.received["user_message"] == "Create a study"


async def test_agent_forwards_tool_progress_and_results(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    """User interfaces show the progress of long tools and structured results (e.g. the findings of a check)."""
    job_id = "66a81f22-e1e5-482f-a504-49ae660e5ece"
    job = {"id": job_id, "study_id": STUDY_ID, "status": "success", "creation_date": "2026-11-13"}
    fake_api.route("GET", f"/v1/launcher/jobs/{job_id}", json_body=job)
    provider = ScriptedProvider(("wait_for_job", {"job_id": job_id}))

    _, events = await collect(AssistantRequest(message="Is my job finished?"), provider, api_client)

    progress = [event for event in events if event["type"] == "tool_progress"]
    assert progress == [
        {"type": "tool_progress", "name": "wait_for_job", "progress": 100, "total": 100, "message": "Job success"}
    ]
    result = events[-1]
    assert result["type"] == "tool_result"
    assert '"finished": true' in result["content"]  # what the model received


def test_system_prompt_is_stable() -> None:
    """No date, no request-specific value: the prompt must stay identical between requests to be cached."""
    assert build_system_prompt(True) == build_system_prompt(True)
    assert "check_study" in build_system_prompt(True)  # includes the instructions of the MCP server


def test_tool_text_cuts_huge_results_with_a_notice() -> None:
    from mcp.types import TextContent

    text = tool_text([TextContent(type="text", text="x" * (MAX_TOOL_RESULT_CHARS + 10))])

    assert len(text) < MAX_TOOL_RESULT_CHARS + 300
    assert "Result cut" in text and "Narrow the request" in text


# ----------------------------------------------------------------------
# Runner (process protocol)
# ----------------------------------------------------------------------


async def test_runner_reports_an_invalid_request() -> None:
    out = io.StringIO()

    await handle('{"message": ""}', out)

    (event,) = [json.loads(line) for line in out.getvalue().splitlines()]
    assert event["type"] == "error"
    assert "Invalid assistant request" in event["message"]


async def test_runner_reports_a_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    out = io.StringIO()

    await handle(json.dumps({"message": "Hello"}), out)

    (event,) = [json.loads(line) for line in out.getvalue().splitlines()]
    assert event["type"] == "error"
    assert "assistant.anthropic_api_key" in event["message"]


async def test_runner_reports_an_unknown_provider() -> None:
    out = io.StringIO()

    await handle(json.dumps({"message": "Hello", "provider": "nope"}), out)

    assert "Available providers: ['anthropic']" in json.loads(out.getvalue())["message"]


# ----------------------------------------------------------------------
# Command-line client
# ----------------------------------------------------------------------


def ndjson(*events: dict[str, Any]) -> httpx2.Response:
    return httpx2.Response(200, text="".join(json.dumps(event) + "\n" for event in events))


def test_cli_client_follows_the_stream() -> None:
    requests: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return ndjson(
            {"type": "tool_call", "name": "list_studies", "input": {}},
            {"type": "tool_result", "name": "list_studies", "is_error": False, "duration_s": 0.1},
            {"type": "done", "answer": "1 study.", "history": [{"role": "user"}], "usage": {}},
        )

    client = AssistantClient("http://antares.test/", "user-token", transport=httpx2.MockTransport(handler))

    done = client.ask("Which studies?", study_id=STUDY_ID, history=[])

    assert done["answer"] == "1 study."
    assert str(requests[0].url) == "http://antares.test/v1/assistant/chat/stream"
    assert requests[0].headers["authorization"] == "Bearer user-token"
    assert json.loads(requests[0].content) == {"message": "Which studies?", "study_id": STUDY_ID, "history": []}


def test_cli_client_errors() -> None:
    responses = iter(
        [
            ndjson({"type": "error", "message": "The Anthropic API key is invalid or revoked."}),
            httpx2.Response(503, json={"description": "No API key for the assistant", "exception": "X"}),
        ]
    )
    client = AssistantClient("http://antares.test", None, transport=httpx2.MockTransport(lambda _: next(responses)))

    with pytest.raises(AssistantClientError, match="API key is invalid"):
        client.ask("Hello", study_id=None, history=[])
    with pytest.raises(AssistantClientError, match="No API key for the assistant"):
        client.ask("Hello", study_id=None, history=[])


def test_describe_tool_call() -> None:
    event = {"name": "get_table", "input": {"study_id": STUDY_ID, "columns": ["a" * 100]}}

    assert describe_tool_call(event).startswith(f"get_table(study_id={STUDY_ID}, columns=[")
    assert describe_tool_call(event).endswith("…)")
