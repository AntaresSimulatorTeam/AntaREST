/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import type { RunStatus } from "@/components/AssistantConversation/useAssistantRun";
import { checkReportSchema, parseJson } from "@/services/api/assistant/schemas";
import type {
  AssistantEvent,
  CheckFinding,
  CheckReport,
  CheckSeverity,
} from "@/services/api/assistant/types";

/** Tool which runs the consistency rules. */
const CHECK_TOOL = "check_study";

export const SEVERITIES: CheckSeverity[] = ["error", "warning", "info"];

/**
 * Steps of a check:
 * - `starting`: the rules are being started
 * - `checking`: the rules run on the study (the only step whose progress is known)
 */
type CheckPhase = "starting" | "checking";

export interface CheckProgress {
  /** Number of rule steps done. */
  current: number;
  total: number;
  /** Rule being checked. */
  rule?: string;
}

/** A check: the rules run on the study, without the AI model. */
export interface StudyCheckState {
  status: RunStatus;
  phase: CheckPhase;
  progress?: CheckProgress;
  /** Findings of the rules. */
  report?: CheckReport;
  /** Why the rules could not run. */
  reportError?: string;
  /** Whether the study can be simulated, deduced from the findings by the server (Markdown). */
  verdict: string;
  error?: string;
}

/** A text written by the AI assistant on request: an explanation, a summary. */
export interface AssistantReportState {
  status: RunStatus;
  /** Text of the assistant (Markdown). */
  answer: string;
  error?: string;
}

/** The review of a study beyond the rules, asked for after the check. */
export interface StudyReviewState extends AssistantReportState {
  /** Number of readings of the study made by the assistant so far. */
  readings: number;
}

/** The findings of one rule: a rule can report several (e.g. a warning and an information). */
export interface RuleGroup {
  rule: string;
  /** The most severe of its findings. */
  severity: CheckSeverity;
  /** Total number of objects concerned. */
  count: number;
  findings: CheckFinding[];
}

export const INITIAL_CHECK_STATE: StudyCheckState = {
  status: "idle",
  phase: "starting",
  verdict: "",
};

export const INITIAL_REPORT_STATE: AssistantReportState = { status: "idle", answer: "" };

export const INITIAL_REVIEW_STATE: StudyReviewState = { ...INITIAL_REPORT_STATE, readings: 0 };

/**
 * Computes the next state of a text asked to the assistant from one of its events.
 *
 * @param state - Current state.
 * @param event - Event received from the assistant.
 * @returns The new state.
 */
export function reduceReportEvent<S extends AssistantReportState>(
  state: S,
  event: AssistantEvent,
): S {
  switch (event.type) {
    case "done":
      return { ...state, status: "success", answer: event.answer };

    case "error":
      return { ...state, status: "error", error: event.message };

    default:
      return state;
  }
}

export function reduceReviewEvent(
  state: StudyReviewState,
  event: AssistantEvent,
): StudyReviewState {
  return event.type === "tool_call"
    ? { ...state, readings: state.readings + 1 }
    : reduceReportEvent(state, event);
}

/**
 * Parses the JSON result of the `check_study` tool.
 *
 * @param content - Result of the tool.
 * @returns The report, or `undefined` if the content is not a report (e.g. cut by the server).
 */
export function parseCheckReport(content: string | undefined): CheckReport | undefined {
  return parseJson(checkReportSchema, content);
}

/**
 * Extracts the rule from a progress message of `check_study` ("Checking hydro_generation_power").
 *
 * @param message - Progress message of the tool.
 * @returns The rule key, if the message ends with one.
 */
export function extractRule(message: string | null | undefined): string | undefined {
  return message?.match(/([a-z]+(?:_[a-z]+)+)\s*$/)?.[1];
}

/**
 * Computes the next state of a check from an event of the server.
 *
 * @param state - Current state of the check.
 * @param event - Event received from the server.
 * @returns The new state.
 */
export function reduceCheckEvent(state: StudyCheckState, event: AssistantEvent): StudyCheckState {
  switch (event.type) {
    case "tool_call":
      return event.name === CHECK_TOOL
        ? { ...state, phase: "checking", progress: undefined }
        : state;

    case "tool_progress":
      return event.name === CHECK_TOOL && event.total
        ? {
            ...state,
            progress: {
              current: event.progress,
              total: event.total,
              rule: extractRule(event.message),
            },
          }
        : state;

    case "tool_result": {
      if (event.name !== CHECK_TOOL) {
        return state;
      }
      const report = event.is_error ? undefined : parseCheckReport(event.content);
      return {
        ...state,
        progress: undefined,
        report,
        reportError: report ? undefined : (event.content ?? ""),
      };
    }

    case "done":
      return { ...state, status: "success", verdict: event.answer };

    case "error":
      return { ...state, status: "error", error: event.message };

    default:
      return state;
  }
}

/**
 * Progress of a running check, in percent.
 *
 * @param state - State of the check.
 * @returns `undefined` when the progress cannot be predicted: only the rules report their
 * progress, the time they take to start is unknown.
 */
export function getProgressPercent(state: StudyCheckState): number | undefined {
  if (state.status !== "running" || state.phase !== "checking") {
    return undefined;
  }
  if (!state.progress) {
    return 0;
  }
  const { current, total } = state.progress;
  return Math.min(100, Math.max(0, Math.round((current / total) * 100)));
}

/**
 * Groups the findings by rule: the user reads, and has explained, one rule at a time, however
 * many findings a rule reports.
 *
 * @param findings - Findings of the rules, most severe first.
 * @returns One group per rule, in the order of their most severe finding.
 */
export function groupFindingsByRule(findings: CheckFinding[]): RuleGroup[] {
  const groups = new Map<string, RuleGroup>();

  for (const finding of findings) {
    const group = groups.get(finding.rule);

    if (group) {
      group.findings.push(finding);
      group.count += finding.count;
      if (SEVERITIES.indexOf(finding.severity) < SEVERITIES.indexOf(group.severity)) {
        group.severity = finding.severity;
      }
    } else {
      groups.set(finding.rule, {
        rule: finding.rule,
        severity: finding.severity,
        count: finding.count,
        findings: [finding],
      });
    }
  }

  return [...groups.values()].sort(
    (a, b) => SEVERITIES.indexOf(a.severity) - SEVERITIES.indexOf(b.severity),
  );
}

/**
 * Describes the findings of a rule for the assistant, when the user starts a conversation about
 * them.
 *
 * @param group - The findings the user is looking at.
 * @returns A note sent before the first message of the user. It is not shown in the conversation.
 */
export function buildRuleContext(group: RuleGroup): string {
  const findings = group.findings.flatMap((finding) => {
    const listed =
      finding.count > finding.objects.length
        ? ` (the first ${finding.objects.length} of ${finding.count})`
        : "";

    return [
      `- ${finding.severity}: ${finding.message}`,
      `  objects concerned${listed}: ${finding.objects.join("; ")}`,
    ];
  });

  return [
    `[The user is looking at what the rule \`${group.rule}\` of the check reported on the study, and writes about it:`,
    ...findings,
    "]",
  ].join("\n");
}

/**
 * Counts the findings which need attention.
 *
 * @param report - Result of the rules, if available.
 * @returns The number of errors and warnings.
 */
export function countIssues(report: CheckReport | undefined): number {
  return report ? report.summary.error + report.summary.warning : 0;
}

/**
 * Severity of the verdict of a check.
 *
 * @param report - Result of the rules.
 * @returns The severity of its most severe findings, `success` without error nor warning.
 */
export function getVerdictSeverity(report: CheckReport): "error" | "warning" | "success" {
  if (report.summary.error > 0) {
    return "error";
  }
  return report.summary.warning > 0 ? "warning" : "success";
}

/**
 * Gives the text of the AI assistant once it is finished.
 *
 * @param state - State of a text asked to the assistant.
 * @returns The text, or `undefined` while it is not written (not asked, running or failed).
 */
export function getFinishedAnswer(state: AssistantReportState): string | undefined {
  return state.status === "success" ? state.answer : undefined;
}

/**
 * Keeps the texts of the AI assistant which are finished.
 *
 * @param states - States of the texts asked to the assistant, by rule.
 * @returns The finished texts, by rule.
 */
export function getFinishedAnswers(
  states: Record<string, AssistantReportState>,
): Record<string, string> {
  return Object.fromEntries(
    Object.entries(states).flatMap(([rule, state]) => {
      const answer = getFinishedAnswer(state);
      return answer === undefined ? [] : [[rule, answer]];
    }),
  );
}
