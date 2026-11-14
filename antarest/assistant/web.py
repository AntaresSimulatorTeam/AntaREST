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

import json
import logging
from collections.abc import Iterator
from typing import Annotated, Any, Literal, TypeAlias

from fastapi import APIRouter, Depends, Query
from starlette.requests import Request
from starlette.responses import StreamingResponse

from antarest.assistant.model import (
    AssistantStatusDTO,
    ChatRequestDTO,
    ChatResponseDTO,
    build_check_prompt,
    build_explain_job_prompt,
)
from antarest.assistant.service import AssistantService
from antarest.core.api_types import UuidStr
from antarest.core.config import Config
from antarest.core.utils.web import APITag
from antarest.dependencies import ConfigDep, auth_required

logger = logging.getLogger(__name__)

ACCESS_TOKEN_COOKIE = "access_token_cookie"  # cookie set by the login endpoint for the web UI


def get_assistant_service(config: ConfigDep) -> AssistantService:
    return AssistantService(config.assistant)


AssistantServiceDep: TypeAlias = Annotated[AssistantService, Depends(get_assistant_service)]


def user_token(request: Request) -> str | None:
    """The token of the caller, forwarded to the agent so that it acts with the caller's permissions."""
    scheme, _, value = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() == "bearer" and value:
        return value
    return request.cookies.get(ACCESS_TOKEN_COOKIE)


def antares_url(request: Request, config: Config) -> str:
    """
    URL used by the agent to call this server back.

    By default the loopback address, on the port which received the request. It never depends on
    the `Host` header: the token of the user is sent to that URL.
    """
    if config.assistant.antares_url:
        return config.assistant.antares_url
    _, port = request.scope["server"]
    return f"http://127.0.0.1:{port}{config.root_path}{config.api_prefix}"


def create_assistant_api() -> APIRouter:
    bp = APIRouter(prefix="/v1", tags=[APITag.assistant], dependencies=[Depends(auth_required)])

    @bp.get("/assistant", summary="Get the status of the AI assistant")
    def get_status(service: AssistantServiceDep) -> AssistantStatusDTO:
        """Tells whether the assistant can be used on this server, and how it is configured."""
        return service.get_status()

    @bp.post("/assistant/chat", summary="Ask the AI assistant")
    def chat(
        request: Request, body: ChatRequestDTO, service: AssistantServiceDep, config: ConfigDep
    ) -> ChatResponseDTO:
        """
        Asks a question to the assistant, an AI agent which reads (or modifies, if the server allows it)
        the studies with the permissions of the caller.

        The answer comes with the list of the tool calls made by the agent, and with a `history`
        to send back with the next message to continue the conversation. An answer can take minutes:
        use `/assistant/chat/stream` to follow its progress.
        """
        logger.info(f"Assistant request (study: {body.study_id})")
        return service.chat(body, antares_url=antares_url(request, config), token=user_token(request))

    @bp.post(
        "/assistant/chat/stream",
        summary="Ask the AI assistant, following its progress",
        response_class=StreamingResponse,
        responses={200: {"content": {"application/x-ndjson": {}}}},
    )
    def chat_stream(
        request: Request, body: ChatRequestDTO, service: AssistantServiceDep, config: ConfigDep
    ) -> StreamingResponse:
        """
        Same as `/assistant/chat`, with the events of the agent sent as they happen, one JSON object
        per line: `tool_call`, `tool_progress`, `tool_result`, `text` (progress notes), then `done`
        (answer, history, usage) or `error`.
        """
        logger.info(f"Assistant request, streamed (study: {body.study_id})")
        # Started here, not in the generator: configuration errors must give an HTTP error status.
        events = service.stream(body, antares_url=antares_url(request, config), token=user_token(request))
        return _ndjson(events)

    @bp.post(
        "/assistant/studies/{study_id}/check",
        summary="Check a study with the AI assistant, following its progress",
        response_class=StreamingResponse,
        responses={200: {"content": {"application/x-ndjson": {}}}},
    )
    def check_study(
        request: Request,
        study_id: UuidStr,
        service: AssistantServiceDep,
        config: ConfigDep,
        language: Annotated[Literal["en", "fr"], Query(description="Language of the report.")] = "en",
    ) -> StreamingResponse:
        """
        Checks the consistency of the inputs of a study before a simulation: the assistant runs the
        deterministic rules of `check_study` (time series included), then explains the findings.

        Same stream of events as `/assistant/chat/stream`. The `tool_progress` events of `check_study`
        give the progress of the rules, its `tool_result` event holds the findings as JSON in `content`,
        and the final `done` event holds the report of the assistant in `answer`.
        """
        logger.info(f"Assistant check of study {study_id}")
        body = ChatRequestDTO(message=build_check_prompt(language), study_id=study_id)
        events = service.stream(body, antares_url=antares_url(request, config), token=user_token(request))
        return _ndjson(events)

    @bp.post(
        "/assistant/jobs/{job_id}/explain",
        summary="Explain why a simulation failed, with the AI assistant",
        response_class=StreamingResponse,
        responses={200: {"content": {"application/x-ndjson": {}}}},
    )
    def explain_job(
        request: Request,
        job_id: UuidStr,
        service: AssistantServiceDep,
        config: ConfigDep,
        language: Annotated[Literal["en", "fr"], Query(description="Language of the explanation.")] = "en",
    ) -> StreamingResponse:
        """
        Explains why a simulation job failed: the assistant runs the deterministic rules of `diagnose_job`
        on the job and its logs, digs further if needed, then explains the probable causes and what to do.

        Same stream of events as `/assistant/chat/stream`. The `tool_result` event of `diagnose_job` holds
        the probable causes and the decisive log lines as JSON in `content`, and the final `done` event
        holds the explanation of the assistant in `answer`.
        """
        logger.info(f"Assistant explanation of job {job_id}")
        body = ChatRequestDTO(message=build_explain_job_prompt(job_id, language))
        events = service.stream(body, antares_url=antares_url(request, config), token=user_token(request))
        return _ndjson(events)

    return bp


def _ndjson(events: Iterator[dict[str, Any]]) -> StreamingResponse:
    def lines() -> Iterator[str]:
        for event in events:
            yield json.dumps(event, ensure_ascii=False) + "\n"

    return StreamingResponse(lines(), media_type="application/x-ndjson")
