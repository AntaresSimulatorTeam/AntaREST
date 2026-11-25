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

import type { AssistantEvent, CheckFinding } from "@/services/api/assistant/types";
import {
  buildRuleContext,
  countIssues,
  extractRule,
  getProgressPercent,
  getVerdictSeverity,
  groupFindingsByRule,
  INITIAL_CHECK_STATE,
  INITIAL_REPORT_STATE,
  INITIAL_REVIEW_STATE,
  parseCheckReport,
  reduceCheckEvent,
  reduceReportEvent,
  reduceReviewEvent,
  type StudyCheckState,
} from "../utils";

const RUNNING_CHECK_STATE: StudyCheckState = { ...INITIAL_CHECK_STATE, status: "running" };

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
  test("follows a whole check: start, rules, findings, verdict", () => {
    expect(getProgressPercent(RUNNING_CHECK_STATE)).toBeUndefined();

    const checking = reduce([CALL]);
    expect(checking.phase).toBe("checking");
    expect(getProgressPercent(checking)).toBe(0);

    const halfway = reduce([progress(2)], checking);
    expect(halfway.progress).toEqual({ current: 2, total: 5, rule: "thermal_availability" });
    expect(getProgressPercent(halfway)).toBe(40);

    const found = reduce([result(REPORT_JSON)], halfway);
    expect(found.report?.findings).toHaveLength(1);
    expect(countIssues(found.report)).toBe(3);

    // The verdict comes with the end of the check: no text of the AI model is awaited
    const done = reduce([{ type: "done", answer: "The study is not ready." }], found);
    expect(done.status).toBe("success");
    expect(done.verdict).toBe("The study is not ready.");
    expect(done.report).toBe(found.report);
  });

  test("keeps the reason when the rules could not run", () => {
    const state = reduce([CALL, result("Antares Web returned HTTP 404: study not found", true)]);

    expect(state.report).toBeUndefined();
    expect(state.reportError).toBe("Antares Web returned HTTP 404: study not found");
  });

  test("stops on an error, keeping the findings already received", () => {
    const state = reduce([
      CALL,
      result(REPORT_JSON),
      { type: "error", message: "The agent of the assistant stopped unexpectedly." },
    ]);

    expect(state.status).toBe("error");
    expect(state.error).toBe("The agent of the assistant stopped unexpectedly.");
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

function finding(rule: string, severity: CheckFinding["severity"], count = 1): CheckFinding {
  return {
    rule,
    severity,
    message: `Message of ${rule} (${severity}).`,
    objects: ["fr", "es"].slice(0, count),
    count,
  };
}

describe("groupFindingsByRule", () => {
  test("makes one group per rule, with its most severe finding and all its objects", () => {
    const groups = groupFindingsByRule([
      finding("thermal_availability", "error", 3),
      finding("unsupplied_energy_cost", "warning", 2),
      finding("disabled_objects", "info", 40),
      finding("unsupplied_energy_cost", "info", 5),
      finding("disabled_objects", "info", 2),
    ]);

    expect(groups.map((group) => [group.rule, group.severity, group.count])).toEqual([
      ["thermal_availability", "error", 3],
      ["unsupplied_energy_cost", "warning", 7],
      ["disabled_objects", "info", 42],
    ]);
    expect(groups[1].findings.map((item) => item.severity)).toEqual(["warning", "info"]);
  });

  test("orders the rules by their most severe finding, whatever the order received", () => {
    const groups = groupFindingsByRule([
      finding("playlist", "info"),
      finding("renewable_series", "warning"),
      finding("renewable_series", "error"),
    ]);

    expect(groups.map((group) => [group.rule, group.severity])).toEqual([
      ["renewable_series", "error"],
      ["playlist", "info"],
    ]);
  });
});

describe("buildRuleContext", () => {
  test("describes the findings of the rule for the assistant: severity, message and objects", () => {
    const [group] = groupFindingsByRule([
      { ...finding("hydro_generation_power", "error", 39), objects: ["fr", "es"] },
      finding("hydro_generation_power", "info"),
    ]);

    const context = buildRuleContext(group);

    expect(context).toContain("rule `hydro_generation_power`");
    expect(context).toContain("- error: Message of hydro_generation_power (error).");
    expect(context).toContain("- info: Message of hydro_generation_power (info).");
    // Only the first objects are listed in a finding
    expect(context).toContain("objects concerned (the first 2 of 39): fr; es");
    expect(context).toContain("objects concerned: fr");
  });
});

describe("getVerdictSeverity", () => {
  test.each([
    [{ error: 1, warning: 2, info: 0 }, "error"],
    [{ error: 0, warning: 2, info: 4 }, "warning"],
    [{ error: 0, warning: 0, info: 4 }, "success"],
  ] as const)("is the one of the most severe findings: %o", (summary, expected) => {
    expect(getVerdictSeverity({ summary, findings: [], notes: [] })).toBe(expected);
  });
});

describe("reduceReportEvent", () => {
  test("keeps the text of the assistant, or the reason of its failure", () => {
    const running = { ...INITIAL_REPORT_STATE, status: "running" as const };

    const ignored = reduceReportEvent(running, { type: "text", text: "Thinking." });
    const done = reduceReportEvent(running, { type: "done", answer: "The rule checks **costs**." });
    const failed = reduceReportEvent(running, { type: "error", message: "No model." });

    expect(ignored).toBe(running);
    expect(done).toEqual({ status: "success", answer: "The rule checks **costs**." });
    expect(failed).toMatchObject({ status: "error", error: "No model." });
  });
});

describe("reduceReviewEvent", () => {
  test("counts the readings of the study, then keeps the observations", () => {
    const events: AssistantEvent[] = [
      { type: "tool_call", name: "survey_study", input: {} },
      { type: "tool_result", name: "survey_study", is_error: false, duration_s: 1 },
      { type: "tool_call", name: "get_table", input: {} },
    ];

    const reading = events.reduce(reduceReviewEvent, {
      ...INITIAL_REVIEW_STATE,
      status: "running",
    });
    const done = reduceReviewEvent(reading, {
      type: "done",
      answer: "Rien d'anormal.",
      history: [],
    });

    expect(reading).toMatchObject({ status: "running", readings: 2, answer: "" });
    expect(done).toMatchObject({ status: "success", answer: "Rien d'anormal." });
  });

  test("keeps the reason of a failure", () => {
    const failed = reduceReviewEvent(INITIAL_REVIEW_STATE, { type: "error", message: "No model." });

    expect(failed).toMatchObject({ status: "error", error: "No model." });
  });
});
