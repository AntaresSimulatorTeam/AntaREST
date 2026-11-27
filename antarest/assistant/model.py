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

from http import HTTPStatus
from typing import Annotated, Any, Literal

from fastapi import HTTPException
from pydantic import Field

from antarest.core.serde import AntaresBaseModel


class AssistantUnavailableError(HTTPException):
    """The assistant cannot be used on this server (disabled, no API key, agent not installed...)."""

    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.SERVICE_UNAVAILABLE, message)


class AssistantError(HTTPException):
    """The assistant could not answer (error of the model API, agent failure, timeout...)."""

    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.BAD_GATEWAY, message)


class AssistantStatusDTO(AntaresBaseModel):
    available: bool
    reason: str = Field(default="", description="Why the assistant is not available.")
    provider: str
    model: str = Field(description="Model id; empty for the default model of the provider.")
    read_only: bool = Field(description="If true, the assistant cannot modify studies nor launch simulations.")


class ChatRequestDTO(AntaresBaseModel, extra="forbid"):
    message: str = Field(min_length=1, description="Question or instruction for the assistant.")
    study_id: str | None = Field(default=None, description="Study the user is working on, if any.")
    history: list[dict[str, Any]] = Field(
        default_factory=list,
        description="`history` of the previous answer, unchanged, to continue a conversation.",
    )


class ToolCallDTO(AntaresBaseModel):
    """A call made by the assistant to a tool of the MCP server."""

    name: str
    input: dict[str, Any]
    is_error: bool = False
    duration_s: float = 0.0


class UsageDTO(AntaresBaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    requests: int = 0


class ChatResponseDTO(AntaresBaseModel):
    answer: str
    tool_calls: list[ToolCallDTO] = Field(description="What the assistant did to answer, in order.")
    history: list[dict[str, Any]] = Field(
        description="Opaque state of the conversation: send it back with the next message."
    )
    provider: str
    model: str
    stop_reason: str = Field(description="'end_turn', 'max_tokens', 'refusal' or 'max_tool_rounds'.")
    usage: UsageDTO


LANGUAGES = {"en": "English", "fr": "French"}


# Bounds of what a client can send back to the model: far above what the rules report.
MAX_FINDINGS = 500
MAX_OBJECTS_PER_FINDING = 100
MAX_FINDING_TEXT = 4000


class FindingDTO(AntaresBaseModel, extra="forbid"):
    """A finding of the rules of the check, as given in the `tool_result` event of `check_study`."""

    rule: str = Field(max_length=100)
    severity: Literal["error", "warning", "info"]
    message: str = Field(max_length=MAX_FINDING_TEXT)
    objects: list[Annotated[str, Field(max_length=MAX_FINDING_TEXT)]] = Field(max_length=MAX_OBJECTS_PER_FINDING)
    count: int = Field(ge=0)


class FindingsRequestDTO(AntaresBaseModel, extra="forbid"):
    findings: list[FindingDTO] = Field(
        max_length=MAX_FINDINGS, description="Findings of the check of the study, unchanged."
    )


class ReviewRequestDTO(AntaresBaseModel, extra="forbid"):
    findings: list[FindingDTO] = Field(
        default_factory=list,
        max_length=MAX_FINDINGS,
        description="Findings of the check of the study, unchanged: the review then does not repeat them.",
    )


EXPLAIN_JOB_PROMPT = """\
A simulation failed: explain why to the user who launched it. The id of the job is {job_id}.

1. Call `diagnose_job` on this job. Call it once.
2. If its probable causes are not enough to explain the failure, read more of the logs with
   `get_job_logs`. When a cause points to the data of the study, look at the object named in the logs
   (for instance with `get_table`, `get_matrix_stats` or `check_study`). Keep it to a few calls.

Then write your explanation, in {language}. The reader is the study engineer who launched the
simulation: an expert of power systems, not of software nor of the solver. Write at most four short
sentences, in two paragraphs:
- First, why the simulation failed, said as a fact about the study: name the object concerned (area,
  plant, link, constraint) and its figures. If the study is not the cause, say that the failure
  comes from the server.
- Then what to do: the one or two concrete things to change in the study, or to contact the
  administrator of Antares Web when the cause is on the server side.

Use the words of the trade, as in the user interface of Antares Web (in French: « groupe » for a
cluster, « zone » for an area, « lien » for a link, « contrainte couplante » for a binding
constraint). Do not quote log lines, error codes, file paths nor tool names: the user interface
shows the probable causes and the log lines next to your explanation. If you are not sure of the
cause, say so in a few words, without listing hypotheses. If the logs do not allow a conclusion, say
so plainly, and say what would be needed to conclude. Do not use Markdown tables, titles nor lists.
"""


def build_explain_job_prompt(job_id: str, language: str) -> str:
    return EXPLAIN_JOB_PROMPT.format(job_id=job_id, language=LANGUAGES[language])
