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
from typing import Any

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


CHECK_LANGUAGES = {"en": "English", "fr": "French"}

CHECK_PROMPT = """\
Check this study before it is simulated, in two steps.

Step 1, the rules. Call `check_study` with `deep` set to true on the study. Call it once.

Step 2, your own review. The rules only catch what they were written for. Look at the study yourself
for what they cannot see: implausible orders of magnitude, values out of line with comparable
objects (for instance one country against its neighbours), settings which contradict what the study
seems to model, things left unfinished. Start with `get_study_context`, `get_study_configuration`,
`describe_monte_carlo_scenarios` and `summarize_installed_capacity`, then dig only where something
looks odd. Keep this review to about fifteen tool calls.

Then write a report for the study engineer, in {language}:
- First, one sentence: is the study ready to be simulated, or what blocks it?
- Under a heading for the findings of the rules: for each finding of severity error or warning, most
  severe first, what it means for the simulation results and what to verify or fix. Then one
  sentence for all the findings of severity info together.
- Under a heading for your other observations: what your own review found. For each one, give the
  figures you read, why they are surprising, and what to confirm. A surprising value is often a
  deliberate modelling choice: present these as questions for the author of the study, and as errors
  only when it is certain. If your review found nothing, say so in one sentence.

The user interface shows the list of findings of the rules and their objects next to your report:
do not repeat the lists of objects, refer to a finding by its rule name. Do not use Markdown tables.
"""


def build_check_prompt(language: str) -> str:
    return CHECK_PROMPT.format(language=CHECK_LANGUAGES[language])


EXPLAIN_JOB_PROMPT = """\
A simulation failed: explain why to the user who launched it. The id of the job is {job_id}.

1. Call `diagnose_job` on this job. Call it once.
2. If its probable causes are not enough to explain the failure, read more of the logs with
   `get_job_logs`. When a cause points to the data of the study, look at the object named in the logs
   (for instance with `get_table`, `get_matrix_stats` or `check_study`). Keep it to a few calls.

Then write your explanation, in {language}:
- First, one sentence: the most probable reason of the failure, and whether it comes from the data of
  the study or from the server.
- Then the reasoning: the evidence found in the logs (quote the decisive lines) and how sure you are.
  If several causes are possible, give the most probable first.
- Last, what to do: concrete steps for the user, and when to contact the administrator of Antares Web
  instead.

If the logs do not allow a conclusion, say so plainly, and say what would be needed to conclude.
The user interface shows the probable causes and the log lines next to your explanation: do not copy
them in full. Do not use Markdown tables.
"""


def build_explain_job_prompt(job_id: str, language: str) -> str:
    return EXPLAIN_JOB_PROMPT.format(job_id=job_id, language=CHECK_LANGUAGES[language])
