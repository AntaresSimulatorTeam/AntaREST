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
Tests of the assistant endpoints. The agent process is replaced by a small script which follows
the same protocol (request on stdin, JSON events on stdout): no model is called.
"""

import json
import sys
from http import HTTPStatus
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.assistant.model import AssistantError, AssistantUnavailableError, ChatRequestDTO
from antarest.assistant.service import AssistantService
from antarest.assistant.web import create_assistant_api
from antarest.core.config import AssistantConfig, Config, SecurityConfig
from antarest.dependencies import AppState

FAKE_AGENT = """
import json, os, sys, time

request = json.load(sys.stdin)

def emit(event):
    print(json.dumps(event), flush=True)

if request["message"] == "crash":
    print("Traceback: boom", file=sys.stderr)
    sys.exit(3)
if request["message"] == "hang":
    time.sleep(60)
if request["message"] == "error":
    emit({"type": "error", "message": "The Anthropic API key is invalid or revoked."})
    sys.exit(0)

emit({"type": "tool_call", "name": "list_studies", "input": {"name": "Base"}})
emit({"type": "tool_result", "name": "list_studies", "is_error": False, "duration_s": 0.5})
emit({"type": "text", "text": "One study found."})
emit({
    "type": "done",
    "answer": "You have 1 study.",
    "history": [{"role": "user", "content": request["message"]}],
    "provider": "anthropic",
    "model": "claude-test",
    "stop_reason": "end_turn",
    "usage": {"input_tokens": 10, "output_tokens": 5, "requests": 2},
    "received": {
        "request": request,
        "api_key": os.environ.get("ANTHROPIC_API_KEY"),
        "virtual_env": os.environ.get("VIRTUAL_ENV"),
    },
})
"""


@pytest.fixture
def agent_command(tmp_path: Path) -> list[str]:
    script = tmp_path / "fake_agent.py"
    script.write_text(FAKE_AGENT)
    return [sys.executable, str(script)]


@pytest.fixture
def assistant_config(agent_command: list[str]) -> AssistantConfig:
    return AssistantConfig.model_validate({"anthropic_api_key": "sk-test", "command": agent_command})


def ask(service: AssistantService, message: str = "Which studies do I have?") -> list[dict[str, Any]]:
    request = ChatRequestDTO(message=message, study_id="study-1")
    return list(service.stream(request, antares_url="http://127.0.0.1:8080", token="user-token"))


# ----------------------------------------------------------------------
# Service
# ----------------------------------------------------------------------


def test_chat_returns_the_answer_and_the_tool_calls(assistant_config: AssistantConfig) -> None:
    service = AssistantService(assistant_config)

    response = service.chat(ChatRequestDTO(message="Which studies do I have?"), antares_url="http://x", token=None)

    assert response.answer == "You have 1 study."
    assert [call.model_dump() for call in response.tool_calls] == [
        {"name": "list_studies", "input": {"name": "Base"}, "is_error": False, "duration_s": 0.5}
    ]
    assert response.history == [{"role": "user", "content": "Which studies do I have?"}]
    assert (response.provider, response.model, response.stop_reason) == ("anthropic", "claude-test", "end_turn")
    assert response.usage.model_dump(exclude_defaults=True) == {"input_tokens": 10, "output_tokens": 5, "requests": 2}


def test_agent_receives_the_user_token_and_the_configuration(
    assistant_config: AssistantConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VIRTUAL_ENV", "/backend/.venv")

    events = ask(AssistantService(assistant_config))

    assert [event["type"] for event in events] == ["tool_call", "tool_result", "text", "done"]
    received = events[-1]["received"]
    assert received["request"] == {
        "message": "Which studies do I have?",
        "history": [],
        "study_id": "study-1",
        "antares_url": "http://127.0.0.1:8080",
        "token": "user-token",
        "read_only": True,
        "provider": "anthropic",
        "model": None,
        "effort": "medium",
        "max_tool_rounds": 40,
    }
    assert received["api_key"] == "sk-test"
    assert received["virtual_env"] is None  # the agent has its own environment


def test_api_key_from_the_environment(agent_command: list[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-from-env")
    service = AssistantService(AssistantConfig(command=agent_command))

    assert service.get_status().available
    assert ask(service)[-1]["received"]["api_key"] == "sk-from-env"


def test_unavailable_without_api_key(agent_command: list[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    service = AssistantService(AssistantConfig(command=agent_command))

    status = service.get_status()
    assert not status.available
    assert "assistant.anthropic_api_key" in status.reason
    with pytest.raises(AssistantUnavailableError, match="No API key"):
        ask(service)


def test_unavailable_when_disabled(agent_command: list[str]) -> None:
    config = AssistantConfig.model_validate({"enabled": False, "anthropic_api_key": "sk", "command": agent_command})

    with pytest.raises(AssistantUnavailableError, match="disabled"):
        ask(AssistantService(config))


@pytest.mark.parametrize(
    "message, expected",
    [
        ("error", "The Anthropic API key is invalid or revoked."),
        ("crash", "stopped unexpectedly"),
    ],
)
def test_chat_errors(assistant_config: AssistantConfig, message: str, expected: str) -> None:
    service = AssistantService(assistant_config)

    with pytest.raises(AssistantError, match=expected) as error:
        service.chat(ChatRequestDTO(message=message), antares_url="http://x", token=None)

    assert error.value.status_code == HTTPStatus.BAD_GATEWAY


def test_agent_is_killed_after_the_timeout(assistant_config: AssistantConfig) -> None:
    service = AssistantService(assistant_config.model_copy(update={"timeout": 1}))

    events = ask(service, "hang")

    assert events == [{"type": "error", "message": "The assistant did not answer within 1 seconds."}]


def test_agent_command_not_found() -> None:
    config = AssistantConfig.model_validate({"anthropic_api_key": "sk", "command": ["/does/not/exist"]})

    (event,) = ask(AssistantService(config))

    assert event["type"] == "error"
    assert "Cannot start the agent" in event["message"]


def test_api_key_is_not_printed_with_the_configuration() -> None:
    config = Config.model_validate({"assistant": {"anthropic_api_key": "sk-secret"}})

    assert config.assistant.anthropic_api_key.get_secret_value() == "sk-secret"
    assert "sk-secret" not in repr(config)


# ----------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------


@pytest.fixture
def client(assistant_config: AssistantConfig) -> TestClient:
    config = Config(security=SecurityConfig(disabled=True), assistant=assistant_config, api_prefix="/api")
    app = FastAPI(title=__name__)
    app.state.app_state = AppState(config=config, services=Mock(), ws_manager=Mock())
    app.include_router(create_assistant_api())
    return TestClient(app)


def test_status_endpoint(client: TestClient) -> None:
    response = client.get("/v1/assistant")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "available": True,
        "reason": "",
        "provider": "anthropic",
        "model": "",
        "read_only": True,
    }


def test_chat_endpoint(client: TestClient) -> None:
    response = client.post("/v1/assistant/chat", json={"message": "Which studies do I have?", "study_id": "s1"})

    assert response.status_code == HTTPStatus.OK, response.text
    body = response.json()
    assert body["answer"] == "You have 1 study."
    assert [call["name"] for call in body["tool_calls"]] == ["list_studies"]


def test_chat_stream_endpoint_forwards_the_bearer_token(client: TestClient) -> None:
    response = client.post(
        "/v1/assistant/chat/stream", json={"message": "Hello"}, headers={"Authorization": "Bearer user-token"}
    )

    assert response.status_code == HTTPStatus.OK, response.text
    assert response.headers["content-type"].startswith("application/x-ndjson")
    events = [json.loads(line) for line in response.text.splitlines()]
    assert [event["type"] for event in events] == ["tool_call", "tool_result", "text", "done"]
    request = events[-1]["received"]["request"]
    assert request["token"] == "user-token"
    # The agent calls the server back on the loopback address, whatever the Host header of the request.
    assert request["antares_url"] == "http://127.0.0.1:80/api"


def test_chat_endpoint_forwards_the_session_cookie(client: TestClient) -> None:
    client.cookies.set("access_token_cookie", "cookie-token")

    response = client.post("/v1/assistant/chat/stream", json={"message": "Hello"})

    assert json.loads(response.text.splitlines()[-1])["received"]["request"]["token"] == "cookie-token"


def test_check_study_endpoint(client: TestClient) -> None:
    study_id = "26543d1b-1ed1-4c62-a5da-5e7f93f8d7bb"

    response = client.post(f"/v1/assistant/studies/{study_id}/check", params={"language": "fr"})

    assert response.status_code == HTTPStatus.OK, response.text
    assert response.headers["content-type"].startswith("application/x-ndjson")
    request = json.loads(response.text.splitlines()[-1])["received"]["request"]
    assert request["study_id"] == study_id
    assert request["history"] == []
    # The prompt is owned by the server: clients only choose the study and the language of the report.
    assert "Call `check_study` with `deep` set to true" in request["message"]
    assert "in French" in request["message"]


def test_check_study_endpoint_rejects_invalid_parameters(client: TestClient) -> None:
    study_id = "26543d1b-1ed1-4c62-a5da-5e7f93f8d7bb"

    bad_language = client.post(f"/v1/assistant/studies/{study_id}/check", params={"language": "de"})
    bad_study_id = client.post("/v1/assistant/studies/..%2Fetc/check")

    assert bad_language.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert bad_study_id.status_code in (HTTPStatus.UNPROCESSABLE_ENTITY, HTTPStatus.NOT_FOUND)


def test_explain_job_endpoint(client: TestClient) -> None:
    job_id = "faad6c7b-e93d-4a4c-9973-c578c5a4202b"

    response = client.post(f"/v1/assistant/jobs/{job_id}/explain", params={"language": "fr"})
    invalid = client.post("/v1/assistant/jobs/not-a-job-id/explain")

    assert response.status_code == HTTPStatus.OK, response.text
    request = json.loads(response.text.splitlines()[-1])["received"]["request"]
    assert request["study_id"] is None
    assert f"The id of the job is {job_id}." in request["message"]
    assert "Call `diagnose_job` on this job" in request["message"]
    assert "in French" in request["message"]
    assert invalid.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_chat_endpoint_errors(client: TestClient) -> None:
    empty = client.post("/v1/assistant/chat", json={"message": ""})
    unknown_field = client.post("/v1/assistant/chat", json={"message": "Hello", "model": "other"})
    failed = client.post("/v1/assistant/chat", json={"message": "error"})

    assert empty.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert unknown_field.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert failed.status_code == HTTPStatus.BAD_GATEWAY
    assert failed.json()["detail"] == "The Anthropic API key is invalid or revoked."


def test_chat_endpoint_without_api_key(agent_command: list[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    config = Config(security=SecurityConfig(disabled=True), assistant=AssistantConfig(command=agent_command))
    app = FastAPI(title=__name__)
    app.state.app_state = AppState(config=config, services=Mock(), ws_manager=Mock())
    app.include_router(create_assistant_api())

    for path in ("/v1/assistant/chat", "/v1/assistant/chat/stream"):
        response = TestClient(app).post(path, json={"message": "Hello"})
        assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
        assert "No API key" in response.json()["detail"]
