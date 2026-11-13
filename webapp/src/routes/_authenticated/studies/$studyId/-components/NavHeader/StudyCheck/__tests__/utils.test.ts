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

import type { AssistantEvent } from "@/services/api/assistant/types";
import {
  countIssues,
  extractRule,
  getProgressPercent,
  parseCheckReport,
  reduceCheckEvent,
  RUNNING_CHECK_STATE,
  type StudyCheckState,
} from "../utils";

const REPORT_JSON = JSON.stringify({
  summary: { error: 1, warning: 2, info: 0 },
  findings: [
    {
      rule: "hydro_generation_power",
      severity: "error",
      message: "Hydro inflows but no generating power.",
      objects: ["fr", "es"],
      count: 39,
    },
  ],
  rules_run: ["calendar", "hydro_generation_power"],
  rules_skipped: [],
  notes: [],
});

function reduce(events: AssistantEvent[], state: StudyCheckState = RUNNING_CHECK_STATE) {
  return events.reduce(reduceCheckEvent, state);
}

const CALL: AssistantEvent = { type: "tool_call", name: "check_study", input: { deep: true } };

function progress(current: number): AssistantEvent {
  return {
    type: "tool_progress",
    name: "check_study",
    progress: current,
    total: 5,
    message: "Checking thermal_availability",
  };
}

function result(content: string, isError = false): AssistantEvent {
  return { type: "tool_result", name: "check_study", is_error: isError, duration_s: 85, content };
}

describe("parseCheckReport", () => {
  test("parses the result of the check_study tool", () => {
    const report = parseCheckReport(REPORT_JSON);

    expect(report?.summary).toEqual({ error: 1, warning: 2, info: 0 });
    expect(report?.findings[0].count).toBe(39);
    expect(report?.rulesRun).toEqual(["calendar", "hydro_generation_power"]);
  });

  test.each([
    undefined,
    "",
    "Error executing tool check_study",
    '{"summary": {}}',
    `${REPORT_JSON.slice(0, 80)}\n[Result cut: 90000 characters]`,
  ])("returns undefined for a content which is not a report: %s", (content) => {
    expect(parseCheckReport(content)).toBeUndefined();
  });
});

describe("extractRule", () => {
  test("reads the rule at the end of a progress message", () => {
    expect(extractRule("Checking hydro_generation_power")).toBe("hydro_generation_power");
    expect(extractRule("Checking")).toBeUndefined();
    expect(extractRule(null)).toBeUndefined();
  });
});

describe("reduceCheckEvent", () => {
  test("follows a whole check: start, rules, findings, analysis", () => {
    expect(getProgressPercent(RUNNING_CHECK_STATE)).toBeUndefined();

    const checking = reduce([CALL]);
    expect(checking.phase).toBe("checking");
    expect(getProgressPercent(checking)).toBe(0);

    const halfway = reduce([progress(2)], checking);
    expect(halfway.progress).toEqual({ current: 2, total: 5, rule: "thermal_availability" });
    expect(getProgressPercent(halfway)).toBe(40);

    // The findings are available before the analysis of the assistant
    const reporting = reduce([result(REPORT_JSON)], halfway);
    expect(reporting.phase).toBe("reporting");
    expect(reporting.status).toBe("running");
    expect(reporting.report?.findings).toHaveLength(1);
    expect(countIssues(reporting.report)).toBe(3);
    expect(getProgressPercent(reporting)).toBeUndefined();

    const done = reduce(
      [
        { type: "tool_call", name: "get_matrix_stats", input: {} },
        { type: "tool_result", name: "get_matrix_stats", is_error: false, duration_s: 1 },
        { type: "text", text: "Looking at the series." },
        { type: "done", answer: "The study **cannot** be simulated as is." },
      ],
      reporting,
    );
    expect(done.status).toBe("success");
    expect(done.answer).toBe("The study **cannot** be simulated as is.");
    expect(done.extraTools).toEqual(["get_matrix_stats"]);
    expect(done.report).toBe(reporting.report);
  });

  test("keeps the reason when the rules could not run", () => {
    const state = reduce([CALL, result("Antares Web returned HTTP 404: study not found", true)]);

    expect(state.report).toBeUndefined();
    expect(state.reportError).toBe("Antares Web returned HTTP 404: study not found");
    expect(state.phase).toBe("reporting");
  });

  test("stops on an error of the assistant, keeping the findings already received", () => {
    const state = reduce([
      CALL,
      result(REPORT_JSON),
      { type: "error", message: "The Anthropic API rate limit is reached." },
    ]);

    expect(state.status).toBe("error");
    expect(state.error).toBe("The Anthropic API rate limit is reached.");
    expect(state.report?.findings).toHaveLength(1);
  });

  test("ignores the progress of other tools", () => {
    const state = reduce([
      CALL,
      { type: "tool_progress", name: "wait_for_job", progress: 50, total: 100, message: null },
    ]);

    expect(state.progress).toBeUndefined();
  });
});
