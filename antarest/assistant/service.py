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
AI assistant service.

The agent (model calls and MCP tools) lives in the `mcp-server` package and runs in its own
process, started for each request: its dependencies stay out of the backend environment, and a
stuck answer is killed without impact on the server. The agent calls back the REST API of this
server with the token of the user, so the permissions of the user apply to everything it does.

Protocol with the agent process: the request as JSON on its stdin, then one JSON event per line
on its stdout, ending with a `done` or `error` event.
"""

import json
import logging
import os
import shutil
import signal
import subprocess
import tempfile
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from antarest.assistant.model import (
    AssistantError,
    AssistantStatusDTO,
    AssistantUnavailableError,
    ChatRequestDTO,
    ChatResponseDTO,
    ToolCallDTO,
    UsageDTO,
)
from antarest.core.config import AssistantConfig

logger = logging.getLogger(__name__)

MCP_SERVER_DIR = Path(__file__).parents[2] / "mcp-server"
AGENT_SCRIPT = "antares-web-assistant"
API_KEY_ENV_VARS = {"anthropic": "ANTHROPIC_API_KEY"}
TERMINAL_EVENTS = {"done", "error"}
LOG_TAIL_CHARS = 4000


class AssistantService:
    def __init__(self, config: AssistantConfig) -> None:
        self.config = config

    def get_status(self) -> AssistantStatusDTO:
        try:
            self._check_available()
            reason = ""
        except AssistantUnavailableError as e:
            reason = str(e.detail)
        return AssistantStatusDTO(
            available=not reason,
            reason=reason,
            provider=self.config.provider,
            model=self.config.model,
            read_only=self.config.read_only,
        )

    def chat(self, request: ChatRequestDTO, *, antares_url: str, token: str | None) -> ChatResponseDTO:
        """Runs one turn of conversation and returns the answer with the trace of the tool calls."""
        tool_calls: list[ToolCallDTO] = []
        for event in self.stream(request, antares_url=antares_url, token=token):
            match event.get("type"):
                case "tool_call":
                    tool_calls.append(ToolCallDTO(name=event["name"], input=event["input"]))
                case "tool_result" if tool_calls:
                    tool_calls[-1].is_error = event["is_error"]
                    tool_calls[-1].duration_s = event["duration_s"]
                case "error":
                    raise AssistantError(event["message"])
                case "done":
                    return ChatResponseDTO(
                        answer=event["answer"],
                        tool_calls=tool_calls,
                        history=event["history"],
                        provider=event["provider"],
                        model=event["model"],
                        stop_reason=event["stop_reason"],
                        usage=UsageDTO.model_validate(event["usage"]),
                    )
        raise AssistantError("The assistant stopped without an answer.")

    def stream(self, request: ChatRequestDTO, *, antares_url: str, token: str | None) -> Iterator[dict[str, Any]]:
        """
        Runs one turn of conversation, yielding the events of the agent as they happen:
        `tool_call`, `tool_result`, `text`, then `done` or `error`.

        Raises:
            AssistantUnavailableError: if the assistant is not configured (raised before the first event).
        """
        command = self._check_available()
        payload = {
            "message": request.message,
            "history": request.history,
            "study_id": request.study_id,
            "antares_url": antares_url,
            "token": token,
            "read_only": self.config.read_only,
            "provider": self.config.provider,
            "model": self.config.model or None,
            "effort": self.config.effort,
            "max_tool_rounds": self.config.max_tool_rounds,
        }
        return self._run_agent(command, payload)

    def _check_available(self) -> list[str]:
        """Returns the command of the agent, or raises if the assistant cannot be used."""
        if not self.config.enabled:
            raise AssistantUnavailableError("The assistant is disabled on this server (`assistant.enabled`).")
        key_variable = API_KEY_ENV_VARS.get(self.config.provider)
        if key_variable and not self._api_key(key_variable):
            raise AssistantUnavailableError(
                f"No API key for the assistant: set `assistant.{self.config.provider}_api_key` in the "
                f"configuration file of the server, or its {key_variable} environment variable."
            )
        if self.config.command:
            return self.config.command
        uv = shutil.which("uv")
        if uv is None or not MCP_SERVER_DIR.is_dir():
            raise AssistantUnavailableError(
                "The agent of the assistant is not installed: `uv` and the `mcp-server` directory are required, "
                "or set `assistant.command` in the configuration file of the server."
            )
        return [uv, "run", "--quiet", "--directory", str(MCP_SERVER_DIR), AGENT_SCRIPT]

    def _api_key(self, variable: str) -> str:
        return self.config.anthropic_api_key.get_secret_value() or os.environ.get(variable, "")

    def _agent_environment(self) -> dict[str, str]:
        environment = dict(os.environ)
        # The agent has its own virtual environment: it must not inherit the one of the backend.
        environment.pop("VIRTUAL_ENV", None)
        key_variable = API_KEY_ENV_VARS.get(self.config.provider)
        if key_variable:
            # Through the environment, never the command line (visible to the other users of the machine).
            environment[key_variable] = self._api_key(key_variable)
        return environment

    def _run_agent(self, command: list[str], payload: dict[str, Any]) -> Iterator[dict[str, Any]]:
        # The logs of the agent go to a file rather than a pipe: nobody reads them while it runs,
        # and a full pipe would block the agent.
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as agent_logs:
            try:
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=agent_logs,
                    text=True,
                    encoding="utf-8",
                    env=self._agent_environment(),
                    # Its own process group, to kill it together with the processes it starts (`uv run` -> python).
                    start_new_session=True,
                )
            except OSError as e:
                logger.error("Cannot start the assistant agent", exc_info=e)
                yield {"type": "error", "message": f"Cannot start the agent of the assistant: {e}"}
                return

            assert process.stdin is not None and process.stdout is not None
            agent_input, agent_output = process.stdin, process.stdout
            timed_out = threading.Event()

            def kill_on_timeout() -> None:
                timed_out.set()
                _kill(process)

            watchdog = threading.Timer(self.config.timeout, kill_on_timeout)
            watchdog.start()
            finished = False
            try:
                try:
                    agent_input.write(json.dumps(payload))
                    agent_input.close()
                except BrokenPipeError:
                    pass  # the agent died at startup: reported below, with its logs
                for line in agent_output:
                    if not line.strip():
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning(f"Ignoring an invalid line from the assistant agent: {line[:200]!r}")
                        continue
                    yield event
                    if event.get("type") in TERMINAL_EVENTS:
                        finished = True
                        break
                if not finished:
                    exit_code = process.wait()
                    agent_logs.seek(0)
                    logger.error(
                        f"Assistant agent stopped with exit code {exit_code}:\n{agent_logs.read()[-LOG_TAIL_CHARS:]}"
                    )
                    if timed_out.is_set():
                        message = f"The assistant did not answer within {self.config.timeout} seconds."
                    else:
                        message = "The agent of the assistant stopped unexpectedly, see the logs of the server."
                    yield {"type": "error", "message": message}
            finally:
                # Also reached when the caller stops reading (client disconnected): do not leave the agent running.
                watchdog.cancel()
                if process.poll() is None:
                    _kill(process)
                process.wait()
                agent_output.close()


def _kill(process: subprocess.Popen[str]) -> None:
    """Kills the agent and its children: `uv run` cannot forward a SIGKILL to the Python process it started."""
    if hasattr(os, "killpg"):
        try:
            os.killpg(process.pid, signal.SIGKILL)
            return
        except ProcessLookupError:
            return  # already finished
    process.kill()
