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

from antarest.assistant.model import AssistantUnavailableError, ChatRequestDTO
from antarest.assistant.service import AssistantService
from antarest.assistant.web import create_assistant_api
from antarest.core.config import AssistantConfig, Config, SecurityConfig
from antarest.dependencies import AppState

FAKE_AGENT = """
import json, os, sys, time

request = json.load(sys.stdin)
message = request.get("message", "")  # the workflows have no message

def emit(event):
    print(json.dumps(event), flush=True)

if message == "crash":
    print("Traceback: boom", file=sys.stderr)
    sys.exit(3)
if message == "hang":
    time.sleep(60)
if message == "error":
    emit({"type": "error", "message": "The model endpoint rejected the API key."})
    sys.exit(0)

emit({"type": "tool_call", "name": "list_studies", "input": {"name": "Base"}})
emit({"type": "tool_result", "name": "list_studies", "is_error": False, "duration_s": 0.5})
emit({"type": "text", "text": "One study found."})
emit({
    "type": "done",
    "answer": "You have 1 study.",
    "history": [{"role": "user", "content": message}],
    "provider": "openai",
    "model": "qwen-test",
    "stop_reason": "end_turn",
    "usage": {"input_tokens": 10, "output_tokens": 5, "requests": 2},
    "received": {
        "request": request,
        "api_key": os.environ.get("OPENAI_API_KEY"),
        "virtual_env": os.environ.get("VIRTUAL_ENV"),
    },
})
"""


@pytest.fixture
def agent_command(tmp_path: Path) -> list[str]:
    script = tmp_path / "fake_agent.py"
    script.write_text(FAKE_AGENT)
    return [sys.executable, str(script)]


MODEL_SERVER = {"base_url": "http://model.test/v1", "model": "qwen-test"}


@pytest.fixture
def assistant_config(agent_command: list[str]) -> AssistantConfig:
    return AssistantConfig.model_validate({**MODEL_SERVER, "api_key": "sk-test", "command": agent_command})


def ask(service: AssistantService, message: str = "Which studies do I have?") -> list[dict[str, Any]]:
    request = ChatRequestDTO(message=message, study_id="study-1")
    return list(service.stream(request, antares_url="http://127.0.0.1:8080", token="user-token"))


# ----------------------------------------------------------------------
# Service
# ----------------------------------------------------------------------


def test_agent_receives_the_user_token_and_the_configuration(
    assistant_config: AssistantConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VIRTUAL_ENV", "/backend/.venv")

    events = ask(AssistantService(assistant_config))

    assert [event["type"] for event in events] == ["tool_call", "tool_result", "text", "done"]
    received = events[-1]["received"]
    assert received["request"] == {
        "task": "chat",
        "message": "Which studies do I have?",
        "history": [],
        "study_id": "study-1",
        "antares_url": "http://127.0.0.1:8080",
        "token": "user-token",
        "read_only": True,
        "provider": "openai",
        "base_url": "http://model.test/v1",
        "model": "qwen-test",
        "max_tool_rounds": 40,
        "writing_reasoning_effort": None,
    }
    assert received["api_key"] == "sk-test"
    assert received["virtual_env"] is None  # the agent has its own environment


def test_endpoint_and_key_from_the_environment(agent_command: list[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """The variables that OpenAI-compatible tools already use on the machine are enough."""
    monkeypatch.setenv("OPENAI_BASE_URL", "http://env.test/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")
    service = AssistantService(AssistantConfig(model="qwen-test", command=agent_command))

    assert service.get_status().available
    received = ask(service)[-1]["received"]
    assert received["request"]["base_url"] == "http://env.test/v1"
    assert received["api_key"] == "sk-from-env"


def test_no_api_key_is_needed_by_a_local_model_server(
    agent_command: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    service = AssistantService(AssistantConfig.model_validate({**MODEL_SERVER, "command": agent_command}))

    assert service.get_status().available
    assert ask(service)[-1]["received"]["api_key"] is None


def test_unavailable_when_disabled(agent_command: list[str]) -> None:
    config = AssistantConfig.model_validate({**MODEL_SERVER, "enabled": False, "command": agent_command})

    with pytest.raises(AssistantUnavailableError, match="disabled"):
        ask(AssistantService(config))


def test_agent_is_killed_after_the_timeout(assistant_config: AssistantConfig) -> None:
    service = AssistantService(assistant_config.model_copy(update={"timeout": 1}))

    events = ask(service, "hang")

    assert events == [{"type": "error", "message": "The assistant did not answer within 1 seconds."}]


def test_agent_command_not_found() -> None:
    config = AssistantConfig.model_validate({**MODEL_SERVER, "command": ["/does/not/exist"]})

    (event,) = ask(AssistantService(config))

    assert event["type"] == "error"
    assert "Cannot start the agent" in event["message"]


def test_api_key_is_not_printed_with_the_configuration() -> None:
    config = Config.model_validate({"assistant": {"api_key": "sk-secret"}})

    assert config.assistant.api_key.get_secret_value() == "sk-secret"
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
        "provider": "openai",
        "model": "qwen-test",
        "read_only": True,
    }


def test_chat_endpoint(client: TestClient) -> None:
    response = client.post("/v1/assistant/chat", json={"message": "Which studies do I have?", "study_id": "s1"})

    assert response.status_code == HTTPStatus.OK, response.text
    body = response.json()
    assert body["answer"] == "You have 1 study."
    assert body["tool_calls"] == [
        {"name": "list_studies", "input": {"name": "Base"}, "is_error": False, "duration_s": 0.5}
    ]
    assert body["history"] == [{"role": "user", "content": "Which studies do I have?"}]
    assert (body["provider"], body["model"], body["stop_reason"]) == ("openai", "qwen-test", "end_turn")
    assert (body["usage"]["input_tokens"], body["usage"]["output_tokens"], body["usage"]["requests"]) == (10, 5, 2)


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


FINDING = {
    "rule": "calendar",
    "severity": "warning",
    "message": "1 January is set to a Monday.",
    "objects": ["settings/generaldata.ini"],
    "count": 1,
}


def test_check_study_endpoint(client: TestClient) -> None:
    study_id = "26543d1b-1ed1-4c62-a5da-5e7f93f8d7bb"

    response = client.post(f"/v1/assistant/studies/{study_id}/check", params={"language": "fr"})

    assert response.status_code == HTTPStatus.OK, response.text
    assert response.headers["content-type"].startswith("application/x-ndjson")
    request = json.loads(response.text.splitlines()[-1])["received"]["request"]
    # The steps of the check belong to the agent: the backend only names the task.
    assert (request["task"], request["study_id"], request["language"]) == ("check", study_id, "fr")
    assert "message" not in request and "findings" not in request


@pytest.mark.parametrize("task", ["explain", "summary"])
def test_findings_of_the_check_are_sent_to_the_agent_to_be_explained(client: TestClient, task: str) -> None:
    study_id = "26543d1b-1ed1-4c62-a5da-5e7f93f8d7bb"
    url = f"/v1/assistant/studies/{study_id}/check/{task}"

    response = client.post(url, params={"language": "fr"}, json={"findings": [FINDING]})
    without_findings = client.post(url)
    unknown_severity = client.post(url, json={"findings": [{**FINDING, "severity": "fatal"}]})
    too_many = client.post(url, json={"findings": [FINDING] * 501})

    assert response.status_code == HTTPStatus.OK, response.text
    request = json.loads(response.text.splitlines()[-1])["received"]["request"]
    assert (request["task"], request["study_id"], request["language"]) == (task, study_id, "fr")
    assert request["findings"] == [FINDING]
    # What goes to the model is validated and bounded before the agent starts.
    assert without_findings.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert unknown_severity.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert too_many.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_review_study_endpoint_knows_the_findings_of_the_check(client: TestClient) -> None:
    study_id = "26543d1b-1ed1-4c62-a5da-5e7f93f8d7bb"

    response = client.post(f"/v1/assistant/studies/{study_id}/review", json={"findings": [FINDING]})
    without_body = client.post(f"/v1/assistant/studies/{study_id}/review")

    assert response.status_code == HTTPStatus.OK, response.text
    request = json.loads(response.text.splitlines()[-1])["received"]["request"]
    assert (request["task"], request["study_id"], request["language"]) == ("review", study_id, "en")
    assert request["findings"] == [FINDING]
    assert without_body.status_code == HTTPStatus.OK, without_body.text
    assert "findings" not in json.loads(without_body.text.splitlines()[-1])["received"]["request"]


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
    crashed = client.post("/v1/assistant/chat", json={"message": "crash"})

    assert empty.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert unknown_field.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert failed.status_code == HTTPStatus.BAD_GATEWAY
    assert failed.json()["detail"] == "The model endpoint rejected the API key."
    assert crashed.status_code == HTTPStatus.BAD_GATEWAY
    assert "stopped unexpectedly" in crashed.json()["detail"]


@pytest.mark.parametrize(
    "assistant, expected",
    [({}, "assistant.base_url"), ({"base_url": "http://model.test/v1"}, "assistant.model")],
)
def test_assistant_is_unavailable_without_a_model_server(
    agent_command: list[str], monkeypatch: pytest.MonkeyPatch, assistant: dict[str, str], expected: str
) -> None:
    """No default server: the content of the studies must not go to a server nobody chose."""
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    assistant_config = AssistantConfig.model_validate({**assistant, "command": agent_command})
    config = Config(security=SecurityConfig(disabled=True), assistant=assistant_config)
    app = FastAPI(title=__name__)
    app.state.app_state = AppState(config=config, services=Mock(), ws_manager=Mock())
    app.include_router(create_assistant_api())

    status = TestClient(app).get("/v1/assistant").json()
    assert not status["available"]
    assert expected in status["reason"]
    for path in ("/v1/assistant/chat", "/v1/assistant/chat/stream"):
        response = TestClient(app).post(path, json={"message": "Hello"})
        assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
        assert expected in response.json()["detail"]
