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

import { checkReportSchema } from "@/services/api/assistant/schemas";
import type { AssistantEvent, CheckReport } from "@/services/api/assistant/types";

/** Tool of the assistant which runs the consistency rules. */
export const CHECK_TOOL = "check_study";

export type CheckStatus = "idle" | "running" | "success" | "error";

/**
 * Steps of a check:
 * - `starting`: the assistant starts and decides what to do
 * - `checking`: the rules run on the study (the only step whose progress is known)
 * - `reporting`: the findings are available, the assistant writes its analysis
 */
export type CheckPhase = "starting" | "checking" | "reporting";

export interface CheckProgress {
  /** Number of rule steps done. */
  current: number;
  total: number;
  /** Rule being checked. */
  rule?: string;
}

export interface StudyCheckState {
  status: CheckStatus;
  phase: CheckPhase;
  progress?: CheckProgress;
  /** Findings of the rules: available before the analysis of the assistant. */
  report?: CheckReport;
  /** Why the rules could not run. */
  reportError?: string;
  /** Other tools used by the assistant to explain the findings. */
  extraTools: string[];
  /** Analysis of the findings by the assistant (Markdown). */
  answer: string;
  error?: string;
}

export const INITIAL_CHECK_STATE: StudyCheckState = {
  status: "idle",
  phase: "starting",
  extraTools: [],
  answer: "",
};

export const RUNNING_CHECK_STATE: StudyCheckState = { ...INITIAL_CHECK_STATE, status: "running" };

/**
 * Parses the JSON result of the `check_study` tool.
 *
 * @param content - Result of the tool, as received by the assistant.
 * @returns The report, or `undefined` if the content is not a report (e.g. cut by the server).
 */
export function parseCheckReport(content: string | undefined): CheckReport | undefined {
  if (!content) {
    return undefined;
  }
  try {
    const result = checkReportSchema.safeParse(JSON.parse(content));
    return result.success ? result.data : undefined;
  } catch {
    return undefined;
  }
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
 * Computes the next state of a check from an event of the assistant.
 *
 * @param state - Current state of the check.
 * @param event - Event received from the assistant.
 * @returns The new state.
 */
export function reduceCheckEvent(state: StudyCheckState, event: AssistantEvent): StudyCheckState {
  switch (event.type) {
    case "tool_call":
      return event.name === CHECK_TOOL
        ? { ...state, phase: "checking", progress: undefined }
        : { ...state, extraTools: [...state.extraTools, event.name] };

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
        phase: "reporting",
        progress: undefined,
        report,
        reportError: report ? undefined : (event.content ?? ""),
      };
    }

    case "done":
      return { ...state, status: "success", progress: undefined, answer: event.answer };

    case "error":
      return { ...state, status: "error", progress: undefined, error: event.message };

    default:
      return state;
  }
}

/**
 * Progress of a running check, in percent.
 *
 * @param state - State of the check.
 * @returns `undefined` when the progress cannot be predicted: only the rules report their
 * progress, the time the assistant takes to start and to write its analysis is unknown.
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
 * Counts the findings which need attention.
 *
 * @param report - Result of the rules, if available.
 * @returns The number of errors and warnings.
 */
export function countIssues(report: CheckReport | undefined): number {
  return report ? report.summary.error + report.summary.warning : 0;
}
