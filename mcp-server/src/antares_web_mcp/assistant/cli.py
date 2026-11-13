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
`antares-assistant`: chat with the Antares Web assistant from a terminal.

It is a client of the `/v1/assistant` endpoints of Antares Web: the model API key and the agent
are on the server side, this command only needs the URL of the server (and a token if the
server requires authentication).
"""

import json
import sys
from typing import Any

import click
import httpx2


class AssistantClientError(Exception):
    pass


def _error_message(response: httpx2.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return f"HTTP {response.status_code}: {response.text[:500]}"
    if isinstance(body, dict):
        return str(body.get("description") or body.get("detail") or body)
    return str(body)


def _short(value: Any, limit: int = 60) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def describe_tool_call(event: dict[str, Any]) -> str:
    arguments = ", ".join(f"{name}={_short(value)}" for name, value in event.get("input", {}).items())
    return f"{event['name']}({arguments})"


class AssistantClient:
    def __init__(self, url: str, token: str | None, *, transport: httpx2.BaseTransport | None = None) -> None:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        # No read timeout: an answer can take minutes, and the server enforces its own limit.
        self._http = httpx2.Client(
            base_url=f"{url.rstrip('/')}/v1",
            headers=headers,
            timeout=httpx2.Timeout(10.0, read=None),
            transport=transport,
        )

    def status(self) -> dict[str, Any]:
        try:
            response = self._http.get("/assistant")
        except httpx2.TransportError as e:
            raise AssistantClientError(f"Cannot reach Antares Web at {self._http.base_url}: {e}") from e
        if response.status_code == 404:
            raise AssistantClientError("This Antares Web server has no assistant (`/v1/assistant` not found).")
        if response.is_error:
            raise AssistantClientError(_error_message(response))
        status: dict[str, Any] = response.json()
        return status

    def ask(self, message: str, *, study_id: str | None, history: list[dict[str, Any]]) -> dict[str, Any]:
        """Sends a message, prints the progress of the agent on stderr, and returns the `done` event."""
        body = {"message": message, "study_id": study_id, "history": history}
        try:
            with self._http.stream("POST", "/assistant/chat/stream", json=body) as response:
                if response.is_error:
                    response.read()
                    raise AssistantClientError(_error_message(response))
                for line in response.iter_lines():
                    if not line.strip():
                        continue
                    event: dict[str, Any] = json.loads(line)
                    match event.get("type"):
                        case "tool_call":
                            click.secho(f"  · {describe_tool_call(event)}", fg="bright_black", err=True)
                        case "tool_result" if event.get("is_error"):
                            click.secho(f"    ✗ {event['name']} failed", fg="yellow", err=True)
                        case "text":
                            click.secho(f"  {event['text']}", fg="bright_black", err=True)
                        case "error":
                            raise AssistantClientError(event["message"])
                        case "done":
                            return event
        except httpx2.TransportError as e:
            raise AssistantClientError(f"Connection to Antares Web lost: {e}") from e
        raise AssistantClientError("The assistant stopped without an answer.")


def _print_answer(done: dict[str, Any]) -> None:
    click.echo(done["answer"])
    usage = done.get("usage", {})
    click.secho(
        f"[{done.get('model')} · {usage.get('requests', 0)} model calls · "
        f"{usage.get('input_tokens', 0) + usage.get('cache_read_input_tokens', 0)} tokens in, "
        f"{usage.get('output_tokens', 0)} out]",
        fg="bright_black",
        err=True,
    )


@click.command()
@click.argument("question", required=False)
@click.option(
    "--url",
    envvar="ANTARES_WEB_URL",
    default="http://localhost:8080",
    show_default=True,
    help="Root URL of the Antares Web server [env: ANTARES_WEB_URL].",
)
@click.option(
    "--token",
    envvar="ANTARES_WEB_TOKEN",
    default=None,
    help="Bearer token; not needed if security is disabled on the server [env: ANTARES_WEB_TOKEN].",
)
@click.option("--study", "study_id", default=None, help="Id of the study the questions are about.")
def main(question: str | None, url: str, token: str | None, study_id: str | None) -> None:
    """
    Ask QUESTION to the Antares Web assistant, or start a conversation if no question is given.

    \b
    antares-assistant "Which studies do I have?"
    antares-assistant --study <study id> "What is this study for? Any inconsistency?"
    antares-assistant        (interactive conversation)
    """
    client = AssistantClient(url, token)
    try:
        status = client.status()
        if not status["available"]:
            raise AssistantClientError(f"The assistant is not available: {status['reason']}")
        if question:
            _print_answer(client.ask(question, study_id=study_id, history=[]))
            return

        mode = "read-only" if status["read_only"] else "read-write"
        click.secho(f"Antares Web assistant ({mode}). Empty line or Ctrl-D to quit.", fg="bright_black", err=True)
        history: list[dict[str, Any]] = []
        while True:
            try:
                message = click.prompt(">", prompt_suffix=" ", default="", show_default=False).strip()
            except (click.Abort, EOFError):
                break
            if not message:
                break
            done = client.ask(message, study_id=study_id, history=history)
            history = done["history"]
            _print_answer(done)
    except AssistantClientError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
