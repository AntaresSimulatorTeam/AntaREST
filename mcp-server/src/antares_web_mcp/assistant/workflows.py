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
Workflows of the assistant: tasks whose steps are fixed by the code instead of chosen by the model.

A model hosted on a private network is smaller than the ones of the vendors: it writes well, but
it is less reliable when it must decide which tool to call, compute, or remember a figure. So for
the tasks we know in advance, the code decides and computes, and the model only writes:

- `check`: the code runs the rules of `check_study` and gives the verdict. The model is not called:
  the findings are shown as they are, at once, even when the model server is down.
- `explain`: the model explains the findings the user picked (those of one rule), without any tool.
- `summary`: the model explains all the errors and warnings together, without any tool. The code
  then verifies that the report names each of them, and adds those it left out: the report is
  faithful to the rules whatever the model wrote.
- `review`: the model looks for what the rules cannot see, with a handful of tools built for that.

The model is only called when the user asks for it. `explain` and `summary` receive the findings
from the caller, which got them from `check`: the rules, which can take minutes on a large study,
run once. What is sent to the model depends on the number of *findings*, and is bounded: adding
rules to `check_study` changes neither the prompts nor this module.
"""

import json
from typing import Literal

from pydantic import ValidationError

from antares_web_mcp.assistant.provider import ChatProvider, ChatResult, ProviderError, TextSink, ToolCaller, Usage
from antares_web_mcp.tools.checks import SEVERITY_ORDER, CheckReport, Finding

Task = Literal["chat", "check", "explain", "summary", "review"]
Language = Literal["en", "fr"]
LANGUAGES: dict[Language, str] = {"en": "English", "fr": "French"}
# The tasks where the model only writes, from findings it is given: it has nothing to decide, so the
# reasoning of a "thinking" model (most of its output, and of the wait) can be turned off for them.
WRITING_TASKS: tuple[Task, ...] = ("explain", "summary")

# Errors and warnings explained by the model, most severe first. The others are listed by the code.
MAX_EXPLAINED_FINDINGS = 20
# The user interface shows all the objects of a finding: the model only needs a few examples.
MAX_OBJECTS_FOR_MODEL = 5
MAX_INFO_FINDINGS_FOR_MODEL = 10
# Findings of one explanation (those of one rule, a handful at most), and what the review is told of the check.
MAX_FINDINGS_PER_EXPLANATION = 10
MAX_KNOWN_FINDINGS = 30

# The only tools of a review. `survey_study` does the comparisons; the others give context to a figure.
REVIEW_TOOLS = (
    "survey_study",
    "get_study_context",
    "get_study_configuration",
    "summarize_installed_capacity",
    "get_table",
    "get_matrix_stats",
)
MAX_REVIEW_ROUNDS = 10


class TaskError(ProviderError):
    """A workflow could not run, with a message that can be shown to the user."""


CHECK_SYSTEM = """\
You are the assistant of Antares Web, a platform to manage Antares Simulator studies (power system
adequacy and economic simulations). You explain to study engineers the findings of the consistency
rules run on their study.

A study contains areas (network nodes, with a load) connected by links. Areas contain thermal
clusters (power plants), renewable clusters and short-term storages. Helper (virtual) areas model
tricks: an optional consumption, an availability counter for binding constraints.
"""

CHECK_MESSAGE = """\
The consistency rules were run on the study. Their result is the JSON below. It is exact and
complete: use only the facts and the figures it contains. Do not add a finding, a cause or a figure
that is not in it, and do not compute anything.

Write a report for the study engineer, in {language}:
1. One sentence saying that {verdict}.
2. For each finding of `to_explain`, in the same order: its rule name between backquotes, what it
   means for the results of the simulation, and what to verify or fix. Two to four sentences each.
3. {info_instruction}

A finding is a possible issue: some are deliberate modelling choices that only the author of the
study can confirm. The user interface shows the objects of each finding next to your report: do not
list them all. Do not use Markdown tables.

```json
{findings}
```
"""

EXPLAIN_MESSAGE = """\
The consistency rules reported the findings below on the study, and the user asks you to explain
them. They are exact: use only the facts and the figures they contain. Do not add a finding, a cause
or a figure that is not in them, and do not compute anything.

Write a short explanation for the study engineer, in {language}, in three paragraphs of one or two
sentences each:
1. What the rule checks, and what the finding means for the results of the simulation.
2. What the objects concerned show: quote a few of them with their figures, do not list them all.
3. What to verify or fix, and in which case this is a deliberate modelling choice rather than an error.

Every figure, year and object name you write must be copied from the findings: no other example, no
difference and no ratio. Do not use Markdown tables nor titles.

```json
{findings}
```
"""

REVIEW_MESSAGE = """\
Review this study for what the consistency rules cannot see, and report in {language}.

Call `survey_study` first: it compares the objects of the study with their peers and returns the
values that are out of line. Its comparisons are exact: do not recompute them. Then use the other
tools only to give context to a figure of the survey, with at most {extra_calls} more calls.

Write a short report: for each observation worth the attention of the author, the figures you read,
why they are surprising and what to confirm. Present them as questions for the author, not as
errors: a surprising value is often a deliberate modelling choice. Do not repeat the findings of
the rules. If nothing is out of line, say so in one sentence. Do not use Markdown tables.
"""
KNOWN_FINDINGS = """
The rules already reported these findings to the user, do not repeat them:
{findings}
"""

NOTHING_BLOCKING: dict[Language, str] = {
    "en": "The study can be simulated: the rules found no error and no warning.",
    "fr": "L'étude peut être simulée : les règles n'ont relevé aucune erreur ni aucun avertissement.",
}
INFO_SUMMARY: dict[Language, str] = {
    "en": "They reported {count} finding(s) of severity info, to read as reminders: {rules}.",
    "fr": "Elles ont signalé {count} constat(s) de gravité info, à lire comme des rappels : {rules}.",
}
NOT_READY: dict[Language, str] = {
    "en": "The study is not ready to be simulated: {errors} to fix or confirm first",
    "fr": "L'étude n'est pas prête à être simulée : {errors} à corriger ou à confirmer d'abord",
}
ALSO_WARNINGS: dict[Language, str] = {"en": ", and {warnings} to check.", "fr": ", et {warnings} à vérifier."}
READY_WITH_WARNINGS: dict[Language, str] = {
    "en": "The study can be simulated, with {warnings} to check before trusting the results.",
    "fr": "L'étude peut être simulée, avec {warnings} à vérifier avant de se fier aux résultats.",
}
SEVERITY_WORDS: dict[Language, dict[str, tuple[str, str]]] = {
    "en": {"error": ("error", "errors"), "warning": ("warning", "warnings")},
    "fr": {"error": ("erreur", "erreurs"), "warning": ("avertissement", "avertissements")},
}
NOT_COVERED: dict[Language, str] = {
    "en": "Findings of the rules not covered above",
    "fr": "Constats des règles non commentés ci-dessus",
}


def _blocking(report: CheckReport) -> list[Finding]:
    return [f for f in report.findings if f.severity in ("error", "warning")]


def report_from(findings: list[Finding]) -> CheckReport:
    """
    The report of findings sent back by a caller. The counts by severity are computed again:
    the verdict never relies on figures the caller could have changed.
    """
    ordered = sorted(findings, key=lambda item: SEVERITY_ORDER[item.severity])
    summary = {severity: sum(1 for f in ordered if f.severity == severity) for severity in SEVERITY_ORDER}
    return CheckReport(summary=summary, findings=ordered, rules_run=[], rules_skipped=[], notes=[])


def _counted(count: int, severity: str, language: Language) -> str:
    singular, plural = SEVERITY_WORDS[language][severity]
    return f"{count} {singular if count == 1 else plural}"


def verdict(report: CheckReport, language: Language) -> str:
    """
    Whether the study can be simulated, deduced from the number of errors and warnings.
    It is a computation, not an opinion: the model never writes it.
    """
    errors, warnings = report.summary.get("error", 0), report.summary.get("warning", 0)
    if errors:
        text = NOT_READY[language].format(errors=_counted(errors, "error", language))
        if not warnings:
            return text + "."
        return text + ALSO_WARNINGS[language].format(warnings=_counted(warnings, "warning", language))
    if warnings:
        return READY_WITH_WARNINGS[language].format(warnings=_counted(warnings, "warning", language))
    infos = [f for f in report.findings if f.severity == "info"]
    if not infos:
        return NOTHING_BLOCKING[language]
    rules = ", ".join(f"`{rule}`" for rule in sorted({f.rule for f in infos}))
    return f"{NOTHING_BLOCKING[language]} {INFO_SUMMARY[language].format(count=len(infos), rules=rules)}"


def _verdict_for_model(report: CheckReport) -> str:
    errors, warnings = report.summary.get("error", 0), report.summary.get("warning", 0)
    if errors:
        return (
            f"the study is not ready to be simulated: {errors} finding(s) of severity error must be fixed "
            "or confirmed first"
        )
    return f"the study can be simulated, but {warnings} warning(s) should be checked before trusting the results"


def build_check_message(report: CheckReport, language: Language) -> str:
    """The message asking the model to explain the findings: its size does not grow with the study."""
    infos = [f for f in report.findings if f.severity == "info"]
    findings = {
        "to_explain": [
            {
                "rule": f.rule,
                "severity": f.severity,
                "message": f.message,
                "objects_concerned": f.count,
                "examples": f.objects[:MAX_OBJECTS_FOR_MODEL],
            }
            for f in _blocking(report)[:MAX_EXPLAINED_FINDINGS]
        ],
        "info": [
            {"rule": f.rule, "message": f.message, "objects_concerned": f.count}
            for f in infos[:MAX_INFO_FINDINGS_FOR_MODEL]
        ],
        "other_info_rules": sorted({f.rule for f in infos[MAX_INFO_FINDINGS_FOR_MODEL:]}),
    }
    info_instruction = (
        "One sentence for all the findings of `info` together."
        if infos
        else "Nothing else: there is no finding of severity info."
    )
    return CHECK_MESSAGE.format(
        language=LANGUAGES[language],
        verdict=_verdict_for_model(report),
        info_instruction=info_instruction,
        findings=json.dumps(findings, ensure_ascii=False, indent=1),
    )


def build_explanation_message(findings: list[Finding], language: Language) -> str:
    """The message asking the model to explain a few findings, with all the objects the rules listed."""
    described = [
        {
            "rule": f.rule,
            "severity": f.severity,
            "message": f.message,
            "objects_concerned": f.count,
            "objects": f.objects,
        }
        for f in findings[:MAX_FINDINGS_PER_EXPLANATION]
    ]
    return EXPLAIN_MESSAGE.format(
        language=LANGUAGES[language], findings=json.dumps(described, ensure_ascii=False, indent=1)
    )


def build_review_message(language: Language, known: list[Finding] | None = None) -> str:
    """The message asking for a review. `known`: the findings of the check, which the review must not repeat."""
    message = REVIEW_MESSAGE.format(language=LANGUAGES[language], extra_calls=MAX_REVIEW_ROUNDS - 2)
    if not known:
        return message
    lines = [f"- `{f.rule}` ({f.severity}): {f.message}" for f in report_from(known).findings[:MAX_KNOWN_FINDINGS]]
    return message + KNOWN_FINDINGS.format(findings="\n".join(lines))


def _cites(answer: str, rule: str) -> bool:
    text = answer.lower()
    return rule in text or rule.replace("_", " ") in text


def complete_report(answer: str, report: CheckReport, language: Language) -> str:
    """Adds to the report of the model the errors and warnings it did not name: none can be lost."""
    missing: list[str] = []
    for f in _blocking(report):
        line = f"- `{f.rule}` ({f.severity}): {f.message}"
        if not _cites(answer, f.rule) and line not in missing:
            missing.append(line)
    if not missing:
        return answer
    return "\n\n".join(part for part in (answer.strip(), f"**{NOT_COVERED[language]}**\n" + "\n".join(missing)) if part)


def _without_model(answer: str, model: str) -> ChatResult:
    return ChatResult(answer=answer, history=[], model=model, stop_reason="end_turn", usage=Usage())


async def run_check(*, study_id: str, language: Language, model: str, call_tool: ToolCaller) -> ChatResult:
    """
    Checks a study: runs the rules and gives the verdict. The model is not called.

    The findings are in the `tool_result` event of `check_study`; the answer is the verdict.

    Raises:
        TaskError: if the rules could not be run.
    """
    outcome = await call_tool("check_study", {"study_id": study_id, "deep": True})
    if outcome.is_error:
        raise TaskError(f"The rules could not be run on this study: {outcome.content}")
    try:
        report = CheckReport.model_validate_json(outcome.content)
    except ValidationError as e:
        raise TaskError("The result of the rules could not be read.") from e
    return _without_model(verdict(report, language), model)


async def run_explanation(
    *,
    findings: list[Finding],
    language: Language,
    provider: ChatProvider,
    call_tool: ToolCaller,
    on_text: TextSink,
) -> ChatResult:
    """
    Explains a few findings of the check (those of one rule), without any tool.

    Raises:
        TaskError: if there is no finding to explain.
        ProviderError: if the model API cannot be used.
    """
    if not findings:
        raise TaskError("No finding to explain.")
    return await provider.run_turn(
        system=CHECK_SYSTEM,
        history=[],
        user_message=build_explanation_message(findings, language),
        tools=[],
        call_tool=call_tool,
        on_text=on_text,
        max_tool_rounds=1,
    )


async def run_summary(
    *,
    findings: list[Finding],
    language: Language,
    model: str,
    provider: ChatProvider,
    call_tool: ToolCaller,
    on_text: TextSink,
) -> ChatResult:
    """
    Explains all the errors and warnings of the check together, without any tool, then adds to the
    report those the model did not name.

    Raises:
        ProviderError: if the model API cannot be used.
    """
    report = report_from(findings)
    if not _blocking(report):
        # Nothing to explain, so nothing to invent: the verdict is the whole report.
        return _without_model(verdict(report, language), model)
    result = await provider.run_turn(
        system=CHECK_SYSTEM,
        history=[],
        user_message=build_check_message(report, language),
        tools=[],
        call_tool=call_tool,
        on_text=on_text,
        max_tool_rounds=1,
    )
    return result.model_copy(update={"answer": complete_report(result.answer, report, language)})
