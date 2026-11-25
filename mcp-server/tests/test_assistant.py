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
from typing import Any, override

import httpx2
import pytest

from antares_web_mcp.assistant.agent import (
    MAX_TOOL_RESULT_CHARS,
    AssistantRequest,
    build_system_prompt,
    run_assistant,
    tool_text,
)
from antares_web_mcp.assistant.cli import AssistantClient, AssistantClientError, describe_tool_call
from antares_web_mcp.assistant.openai_provider import OpenAICompatibleProvider
from antares_web_mcp.assistant.provider import (
    ChatResult,
    ProviderError,
    TextSink,
    ToolCaller,
    ToolOutcome,
    ToolSpec,
    Usage,
)
from antares_web_mcp.assistant.providers import build_provider
from antares_web_mcp.assistant.runner import handle
from antares_web_mcp.client import AntaresWebClient
from tests.fake_antares_web import FakeAntaresWeb
from tests.helpers import STUDY_ID, study

TOOLS = [ToolSpec(name="list_studies", description="Find studies.", input_schema={"type": "object", "properties": {}})]
MODEL = "qwen3.8-27b"


def model_response(message: dict[str, Any], finish_reason: str = "stop") -> httpx2.Response:
    """An answer of the chat completions API."""
    body = {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "model": MODEL,
        "choices": [{"index": 0, "message": {"role": "assistant", **message}, "finish_reason": finish_reason}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 20, "prompt_tokens_details": {"cached_tokens": 50}},
    }
    return httpx2.Response(200, json=body)


def tool_call(arguments: str = '{"name": "Base"}') -> dict[str, Any]:
    return {"id": "call_1", "type": "function", "function": {"name": "list_studies", "arguments": arguments}}


class FakeModelApi:
    """Stands for an OpenAI-compatible server: returns the scripted responses in order and records the requests."""

    def __init__(self, *responses: httpx2.Response) -> None:
        self.responses = list(responses)
        self.requests: list[httpx2.Request] = []

    def handler(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        return self.responses.pop(0)

    def bodies(self) -> list[dict[str, Any]]:
        return [json.loads(request.content) for request in self.requests]

    def provider(self) -> OpenAICompatibleProvider:
        client = httpx2.AsyncClient(base_url="http://model.test/v1/", transport=httpx2.MockTransport(self.handler))
        return OpenAICompatibleProvider(client, model=MODEL)


async def run_turn(provider: OpenAICompatibleProvider, **overrides: Any) -> tuple[ChatResult, list[Any]]:
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
# Provider for OpenAI-compatible servers
# ----------------------------------------------------------------------


async def test_provider_runs_the_tool_loop() -> None:
    api = FakeModelApi(
        model_response({"content": "Let me look.", "tool_calls": [tool_call()]}, "tool_calls"),
        model_response({"content": "You have 1 study."}),
    )

    result, seen = await run_turn(api.provider())

    assert result.answer == "You have 1 study."
    assert (result.stop_reason, result.model) == ("end_turn", MODEL)
    assert seen == ["Let me look.", ("list_studies", {"name": "Base"})]
    assert result.usage == Usage(input_tokens=200, output_tokens=40, cache_read_input_tokens=100, requests=2)

    assert str(api.requests[0].url) == "http://model.test/v1/chat/completions"
    first, second = api.bodies()
    assert first["model"] == MODEL
    assert first["messages"][0] == {"role": "system", "content": "You are a test."}
    assert first["tools"] == [
        {
            "type": "function",
            "function": {"name": "list_studies", "description": "Find studies.", "parameters": TOOLS[0].input_schema},
        }
    ]
    # The second request carries the first answer, with its tool call, and the result of the call.
    assert [message["role"] for message in second["messages"]] == ["system", "user", "assistant", "tool"]
    assert second["messages"][2]["tool_calls"] == [tool_call()]
    assert second["messages"][3] == {"role": "tool", "tool_call_id": "call_1", "content": '[{"name": "Base case"}]'}
    # The history is plain JSON: it goes through the Antares Web endpoint and comes back as is.
    assert json.loads(json.dumps(result.history)) == result.history
    # The instructions are not part of it: they are sent again with each message.
    assert [message["role"] for message in result.history] == ["user", "assistant", "tool", "assistant"]


async def test_provider_sends_the_reasoning_effort_only_when_asked() -> None:
    default, quiet = (
        FakeModelApi(model_response({"content": "Yes."})),
        FakeModelApi(model_response({"content": "Yes."})),
    )
    client = httpx2.AsyncClient(base_url="http://model.test/v1/", transport=httpx2.MockTransport(quiet.handler))

    await run_turn(default.provider())
    await run_turn(OpenAICompatibleProvider(client, model=MODEL, reasoning_effort="none"))

    # Not sent by default: a server which does not know the parameter could reject the request.
    assert "reasoning_effort" not in default.bodies()[0]
    assert quiet.bodies()[0]["reasoning_effort"] == "none"


async def test_provider_continues_a_conversation() -> None:
    api = FakeModelApi(model_response({"content": "Yes."}))
    history = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]

    result, _ = await run_turn(api.provider(), history=history, user_message="Still there?")

    assert api.bodies()[0]["messages"][1:] == [*history, {"role": "user", "content": "Still there?"}]
    assert len(result.history) == 4


async def test_provider_keeps_the_reasoning_of_the_model_out_of_the_answer() -> None:
    """Some servers leave the reasoning of the model inline (Qwen, DeepSeek...), others give it apart."""
    message = {"content": "<think>\nThe user wants a list.\n</think>\n\nYou have 1 study.", "reasoning_content": "Hmm."}
    api = FakeModelApi(model_response(message))

    result, _ = await run_turn(api.provider())

    assert result.answer == "You have 1 study."
    assert result.history[-1] == {"role": "assistant", "content": "You have 1 study."}


async def test_provider_gives_unusable_arguments_back_to_the_model() -> None:
    """A small model can write broken JSON: it gets the error as the result of its call, and can try again."""
    api = FakeModelApi(
        model_response({"content": None, "tool_calls": [tool_call('{"name": ')]}, "tool_calls"),
        model_response({"content": "You have 1 study."}),
    )

    result, seen = await run_turn(api.provider())

    assert seen == []  # the tool was not called
    assert "not a JSON object" in api.bodies()[1]["messages"][-1]["content"]
    assert result.answer == "You have 1 study."


async def test_provider_stops_after_max_tool_rounds() -> None:
    api = FakeModelApi(*(model_response({"tool_calls": [tool_call("{}")]}, "tool_calls") for _ in range(3)))

    result, seen = await run_turn(api.provider(), max_tool_rounds=2)

    assert result.stop_reason == "max_tool_rounds"
    assert "Stopped after 2 rounds" in result.answer
    assert len(seen) == 3


async def test_provider_tells_when_the_answer_was_cut() -> None:
    api = FakeModelApi(model_response({"content": "The study has"}, "length"))

    result, _ = await run_turn(api.provider())

    assert result.stop_reason == "max_tokens"
    assert result.answer.startswith("The study has") and "was cut" in result.answer


@pytest.mark.parametrize(
    "status, expected",
    [
        (401, "rejected the API key"),
        (404, "HTTP 404.*no such model"),
        (429, "quota or the rate limit"),
        (500, "HTTP 500.*no such model"),
    ],
)
async def test_provider_errors(status: int, expected: str) -> None:
    api = FakeModelApi(httpx2.Response(status, json={"error": {"message": "no such model"}}))

    with pytest.raises(ProviderError, match=expected):
        await run_turn(api.provider())


async def test_provider_tells_when_the_server_cannot_be_reached() -> None:
    def unreachable(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("certificate verify failed", request=request)

    client = httpx2.AsyncClient(base_url="http://model.test/v1/", transport=httpx2.MockTransport(unreachable))

    with pytest.raises(ProviderError, match="Cannot reach .*model.test.*certificate verify failed"):
        await run_turn(OpenAICompatibleProvider(client, model=MODEL))


def test_build_provider_needs_the_endpoint_and_the_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    provider = build_provider("openai", model=MODEL, base_url="http://model.test/v1")

    assert isinstance(provider, OpenAICompatibleProvider)
    with pytest.raises(ProviderError, match="assistant.base_url"):
        build_provider("openai", model=MODEL, base_url=None)
    with pytest.raises(ProviderError, match="assistant.model"):
        build_provider("openai", model=None, base_url="http://model.test/v1")
    with pytest.raises(ProviderError, match=r"Available providers: \['openai'\]"):
        build_provider("nope", model=MODEL, base_url="http://model.test/v1")


# ----------------------------------------------------------------------
# Agent: provider + MCP tools
# ----------------------------------------------------------------------


class ScriptedProvider:
    """A provider that calls the given tools, then answers with their results."""

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
    fake_api.route("GET", "/v1/studies", json_body={STUDY_ID: study()})
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


async def test_agent_reports_a_provider_error_as_is(api_client: AntaresWebClient) -> None:
    """The message for the user (e.g. an invalid API key) must not be lost in an `ExceptionGroup`."""

    class FailingProvider(ScriptedProvider):
        @override
        async def run_turn(self, **_: Any) -> ChatResult:
            raise ProviderError("The model endpoint rejected the API key.")

    with pytest.raises(ProviderError, match="rejected the API key"):
        await collect(AssistantRequest(message="Hello"), FailingProvider(), api_client)


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


@pytest.mark.parametrize(
    "request_, expected",
    [
        ({"message": ""}, "Invalid assistant request"),
        ({"message": "Hello"}, "assistant.base_url"),  # no model endpoint given by the backend
        ({"message": "Hello", "provider": "nope"}, "Available providers: ['openai']"),
    ],
)
async def test_runner_reports_errors(request_: dict[str, Any], expected: str) -> None:
    out = io.StringIO()

    await handle(json.dumps(request_), out)

    (event,) = [json.loads(line) for line in out.getvalue().splitlines()]
    assert event["type"] == "error"
    assert expected in event["message"]


@pytest.mark.parametrize(
    "task, expected",
    [
        ({"task": "explain", "findings": []}, "none"),
        ({"task": "summary", "findings": []}, "none"),
        # Where the model decides (tools to call, what to look at), its reasoning is kept.
        ({"task": "review"}, None),
        ({"task": "chat", "message": "Hello"}, None),
    ],
)
async def test_runner_turns_the_reasoning_off_for_the_writing_tasks_only(
    task: dict[str, Any], expected: str | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    built: list[str | None] = []

    def build(name: str, *, model: str | None, base_url: str | None, reasoning_effort: str | None) -> Any:
        built.append(reasoning_effort)
        raise ProviderError("stop here")

    monkeypatch.setattr("antares_web_mcp.assistant.runner.build_provider", build)

    await handle(json.dumps({"study_id": STUDY_ID, "writing_reasoning_effort": "none"} | task), io.StringIO())

    assert built == [expected]


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
            ndjson({"type": "error", "message": "The model endpoint rejected the API key."}),
            httpx2.Response(503, json={"description": "No model endpoint for the assistant", "exception": "X"}),
        ]
    )
    client = AssistantClient("http://antares.test", None, transport=httpx2.MockTransport(lambda _: next(responses)))

    with pytest.raises(AssistantClientError, match="rejected the API key"):
        client.ask("Hello", study_id=None, history=[])
    with pytest.raises(AssistantClientError, match="No model endpoint for the assistant"):
        client.ask("Hello", study_id=None, history=[])


def test_describe_tool_call() -> None:
    event = {"name": "get_table", "input": {"study_id": STUDY_ID, "columns": ["a" * 100]}}

    assert describe_tool_call(event).startswith(f"get_table(study_id={STUDY_ID}, columns=[")
    assert describe_tool_call(event).endswith("…)")
