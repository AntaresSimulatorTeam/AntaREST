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
Tests of the workflows of the assistant: the steps are fixed by the code, so that a small model only
has to write, only when the user asks for it, and the reports stay faithful to the rules whatever it writes.
"""

from typing import Any

import pytest
from pydantic import ValidationError

from antares_web_mcp.assistant.agent import AssistantRequest
from antares_web_mcp.assistant.provider import ProviderError
from antares_web_mcp.assistant.workflows import (
    MAX_EXPLAINED_FINDINGS,
    MAX_FINDINGS_PER_EXPLANATION,
    MAX_OBJECTS_FOR_MODEL,
    REVIEW_TOOLS,
    build_check_message,
    build_explanation_message,
    complete_report,
    report_from,
    verdict,
)
from antares_web_mcp.client import AntaresWebClient
from antares_web_mcp.tools.checks import CheckReport, Finding
from tests.fake_antares_web import FakeAntaresWeb
from tests.helpers import STUDY_ID
from tests.test_assistant import ScriptedProvider, collect
from tests.test_checks import route_study, thermal


def finding(rule: str, severity: str = "warning", objects: int = 1) -> Finding:
    return Finding.model_validate(
        {
            "rule": rule,
            "severity": severity,
            "message": f"Message of {rule}.",
            "objects": [f"object {i}" for i in range(min(objects, 30))],
            "count": objects,
        }
    )


def report(*findings: Finding) -> CheckReport:
    summary = {s: sum(1 for f in findings if f.severity == s) for s in ("error", "warning", "info")}
    return CheckReport(summary=summary, findings=list(findings), rules_run=[], rules_skipped=[], notes=[])


# ----------------------------------------------------------------------
# Check: the code runs the rules and gives the verdict, without the model
# ----------------------------------------------------------------------


async def test_check_runs_the_rules_and_never_calls_the_model(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient
) -> None:
    route_study(fake_api)  # 1 error (thermal_min_stable_power), 1 info (unsupplied_energy_cost)
    provider = ScriptedProvider()

    result, events = await collect(AssistantRequest(task="check", study_id=STUDY_ID), provider, api_client)

    # The user interface reads the findings in the events of the tool.
    assert events[0] == {"type": "tool_call", "name": "check_study", "input": {"study_id": STUDY_ID, "deep": True}}
    (findings,) = [event for event in events if event["type"] == "tool_result"]
    assert (findings["name"], findings["is_error"]) == ("check_study", False)
    assert '"thermal_min_stable_power"' in findings["content"]
    # The findings and the verdict do not depend on the model: it is not called.
    assert provider.received == {}
    assert result.usage.requests == 0
    assert result.answer == "The study is not ready to be simulated: 1 error to fix or confirm first."


async def test_check_without_error_nor_warning_says_the_study_can_be_simulated(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient
) -> None:
    base = route_study(fake_api)
    del fake_api.routes[("GET", f"{base}/table-mode/areas")], fake_api.routes[("GET", f"{base}/table-mode/thermals")]
    fake_api.route("GET", f"{base}/table-mode/areas", json_body={"fr": {"energyCostUnsupplied": 10000.0}})
    fake_api.route("GET", f"{base}/table-mode/thermals", json_body={"fr / nuclear": thermal()})

    result, _ = await collect(
        AssistantRequest(task="check", study_id=STUDY_ID, language="fr"), ScriptedProvider(), api_client
    )

    assert "aucun" in result.answer.lower()


async def test_check_fails_when_the_rules_cannot_run(api_client: AntaresWebClient) -> None:
    # No route in the fake server: the study cannot be read.
    with pytest.raises(ProviderError, match="rules could not be run"):
        await collect(AssistantRequest(task="check", study_id=STUDY_ID), ScriptedProvider(), api_client)


def test_tasks_validate_their_inputs() -> None:
    with pytest.raises(ValidationError, match="study_id"):
        AssistantRequest(task="check")
    with pytest.raises(ValidationError, match="message"):
        AssistantRequest(task="chat")
    with pytest.raises(ValidationError, match="findings"):
        AssistantRequest(task="explain", study_id=STUDY_ID)
    with pytest.raises(ValidationError, match="findings"):
        AssistantRequest(task="summary", study_id=STUDY_ID)


def test_verdict_is_computed_from_the_number_of_errors_and_warnings() -> None:
    errors = report(finding("a", "error"), finding("b", "error"), finding("c"))
    warnings = report(finding("c"), finding("d", "info"))
    infos = report(finding("d", "info"))

    assert verdict(errors, "en") == (
        "The study is not ready to be simulated: 2 errors to fix or confirm first, and 1 warning to check."
    )
    assert verdict(errors, "fr") == (
        "L'étude n'est pas prête à être simulée : 2 erreurs à corriger ou à confirmer d'abord, "
        "et 1 avertissement à vérifier."
    )
    assert verdict(warnings, "fr") == (
        "L'étude peut être simulée, avec 1 avertissement à vérifier avant de se fier aux résultats."
    )
    assert "no error and no warning" in verdict(infos, "en") and "`d`" in verdict(infos, "en")
    assert verdict(report(), "en") == "The study can be simulated: the rules found no error and no warning."


def test_report_of_a_caller_is_counted_again() -> None:
    """`explain` and `summary` get their findings from the caller: the counts are never taken from it."""
    rebuilt = report_from([finding("playlist", "info"), finding("calendar"), finding("thermal_availability", "error")])

    assert rebuilt.summary == {"error": 1, "warning": 1, "info": 1}
    assert [f.severity for f in rebuilt.findings] == ["error", "warning", "info"]


# ----------------------------------------------------------------------
# Explanation: the model explains the findings of one rule, on request
# ----------------------------------------------------------------------


async def test_explanation_gives_the_findings_and_no_tool_to_the_model(api_client: AntaresWebClient) -> None:
    provider = ScriptedProvider()
    findings = [finding("unsupplied_energy_cost", objects=3), finding("unsupplied_energy_cost", "info")]
    request = AssistantRequest(task="explain", study_id=STUDY_ID, language="fr", findings=findings)

    _, events = await collect(request, provider, api_client)

    assert provider.received["tools"] == []
    message = provider.received["user_message"]
    assert message.count('"rule": "unsupplied_energy_cost"') == 2
    assert "object 2" in message and "French" in message
    # The rules are not run again: the findings come from the check.
    assert [event["type"] for event in events] == ["text"]


async def test_explanation_needs_a_finding(api_client: AntaresWebClient) -> None:
    request = AssistantRequest(task="explain", study_id=STUDY_ID, findings=[])

    with pytest.raises(ProviderError, match="No finding"):
        await collect(request, ScriptedProvider(), api_client)


def test_explanation_message_is_bounded() -> None:
    many = [finding("disabled_objects", "info", objects=500) for _ in range(50)]

    message = build_explanation_message(many, "en")

    assert message.count('"rule"') == MAX_FINDINGS_PER_EXPLANATION
    assert '"objects_concerned": 500' in message  # the total is given, with the objects the rule listed
    assert len(message) < 12_000


# ----------------------------------------------------------------------
# Summary: the model explains all the errors and warnings, on request
# ----------------------------------------------------------------------


async def test_summary_gives_the_verdict_to_the_model_and_keeps_every_error(api_client: AntaresWebClient) -> None:
    provider = ScriptedProvider()
    findings = [finding("playlist", "info"), finding("thermal_min_stable_power", "error")]
    request = AssistantRequest(task="summary", study_id=STUDY_ID, findings=findings)

    result, events = await collect(request, provider, api_client)

    assert provider.received["tools"] == []
    assert "thermal_min_stable_power" in provider.received["user_message"]
    assert "not ready" in provider.received["user_message"]
    assert not [event for event in events if event["type"] == "tool_call"]
    # The scripted model wrote nothing: the error is still in the report.
    assert "`thermal_min_stable_power` (error)" in result.answer


async def test_summary_without_error_nor_warning_does_not_call_the_model(api_client: AntaresWebClient) -> None:
    provider = ScriptedProvider()
    request = AssistantRequest(task="summary", study_id=STUDY_ID, language="fr", findings=[finding("playlist", "info")])

    result, _ = await collect(request, provider, api_client)

    assert provider.received == {}  # nothing to explain: nothing to invent either
    assert result.usage.requests == 0
    assert "aucun" in result.answer.lower()


def test_report_always_names_the_errors_and_warnings() -> None:
    findings = report(finding("thermal_availability", "error"), finding("calendar"), finding("playlist", "info"))

    complete = complete_report("The **thermal availability** is null: fix the series.", findings, "en")
    untouched = complete_report("See `thermal_availability` and `calendar`.", findings, "en")

    assert "`calendar` (warning): Message of calendar." in complete
    assert "thermal_availability` (error)" not in complete  # cited with spaces: counted as explained
    assert "playlist" not in complete  # findings of severity info are only summarised
    assert untouched == "See `thermal_availability` and `calendar`."


def test_check_message_stays_small_when_rules_and_findings_grow() -> None:
    """More rules means more findings: what goes to the model must stay bounded."""
    many = [finding(f"rule_{i}", "warning", objects=500) for i in range(100)]
    many += [finding(f"info_{i}", "info", objects=500) for i in range(100)]

    message = build_check_message(report(*many), "fr")

    assert message.count('"rule": "rule_') == MAX_EXPLAINED_FINDINGS
    assert f"object {MAX_OBJECTS_FOR_MODEL - 1}" in message and f"object {MAX_OBJECTS_FOR_MODEL}" not in message
    assert "info_0" in message and '"info_99"' in message  # by name and count only
    assert "French" in message
    assert len(message) < 12_000


# ----------------------------------------------------------------------
# Review: the model explores, with a handful of tools
# ----------------------------------------------------------------------


async def test_review_gives_few_tools_and_continues_the_check(api_client: AntaresWebClient) -> None:
    provider = ScriptedProvider()
    history: list[dict[str, Any]] = [{"q": "check"}]

    result, _ = await collect(AssistantRequest(task="review", study_id=STUDY_ID, history=history), provider, api_client)

    assert set(provider.received["tools"]) == set(REVIEW_TOOLS)
    assert "survey_study" in REVIEW_TOOLS and len(REVIEW_TOOLS) <= 6
    assert "survey_study" in provider.received["user_message"]
    assert "already reported" not in provider.received["user_message"]
    assert result.history[0] == {"q": "check"}


async def test_review_is_told_the_findings_of_the_check(api_client: AntaresWebClient) -> None:
    provider = ScriptedProvider()
    request = AssistantRequest(task="review", study_id=STUDY_ID, findings=[finding("calendar")])

    await collect(request, provider, api_client)

    assert "already reported" in provider.received["user_message"]
    assert "- `calendar` (warning): Message of calendar." in provider.received["user_message"]
