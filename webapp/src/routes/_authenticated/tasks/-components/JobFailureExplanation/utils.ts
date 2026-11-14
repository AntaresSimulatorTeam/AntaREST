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

import { jobDiagnosisSchema } from "@/services/api/assistant/schemas";
import type { AssistantEvent, JobDiagnosis } from "@/services/api/assistant/types";

/** Tool of the assistant which finds the probable causes of a failure. */
export const DIAGNOSE_TOOL = "diagnose_job";

export type ExplanationStatus = "idle" | "running" | "success" | "error";

/**
 * Steps of an explanation:
 * - `starting`: the assistant starts
 * - `diagnosing`: the rules read the job and its logs
 * - `explaining`: the probable causes are available, the assistant digs and writes
 */
export type ExplanationPhase = "starting" | "diagnosing" | "explaining";

export interface JobExplanationState {
  status: ExplanationStatus;
  phase: ExplanationPhase;
  /** Probable causes found by the rules: available before the explanation of the assistant. */
  diagnosis?: JobDiagnosis;
  /** Why the rules could not run. */
  diagnosisError?: string;
  /** Other tools used by the assistant to dig further. */
  extraTools: string[];
  /** Explanation written by the assistant (Markdown). */
  answer: string;
  error?: string;
}

export const INITIAL_EXPLANATION_STATE: JobExplanationState = {
  status: "idle",
  phase: "starting",
  extraTools: [],
  answer: "",
};

export const RUNNING_EXPLANATION_STATE: JobExplanationState = {
  ...INITIAL_EXPLANATION_STATE,
  status: "running",
};

/**
 * Parses the JSON result of the `diagnose_job` tool.
 *
 * @param content - Result of the tool, as received by the assistant.
 * @returns The diagnosis, or `undefined` if the content is not one.
 */
export function parseJobDiagnosis(content: string | undefined): JobDiagnosis | undefined {
  if (!content) {
    return undefined;
  }
  try {
    const result = jobDiagnosisSchema.safeParse(JSON.parse(content));
    return result.success ? result.data : undefined;
  } catch {
    return undefined;
  }
}

/**
 * Computes the next state of an explanation from an event of the assistant.
 *
 * @param state - Current state of the explanation.
 * @param event - Event received from the assistant.
 * @returns The new state.
 */
export function reduceExplanationEvent(
  state: JobExplanationState,
  event: AssistantEvent,
): JobExplanationState {
  switch (event.type) {
    case "tool_call":
      return event.name === DIAGNOSE_TOOL
        ? { ...state, phase: "diagnosing" }
        : { ...state, extraTools: [...state.extraTools, event.name] };

    case "tool_result": {
      if (event.name !== DIAGNOSE_TOOL) {
        return state;
      }
      const diagnosis = event.is_error ? undefined : parseJobDiagnosis(event.content);
      return {
        ...state,
        phase: "explaining",
        diagnosis,
        diagnosisError: diagnosis ? undefined : (event.content ?? ""),
      };
    }

    case "done":
      return { ...state, status: "success", answer: event.answer };

    case "error":
      return { ...state, status: "error", error: event.message };

    default:
      return state;
  }
}
