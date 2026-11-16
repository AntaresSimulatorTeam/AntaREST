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

import { getAssistantStatus, streamLogsExplanation } from "@/services/api/assistant";
import type { AssistantEvent, StreamLogsExplanationParams } from "@/services/api/assistant/types";
import { createQueryClient, createQueryWrapper, deferred } from "@/tests/queryUtils";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import LogsExplanation from "..";

vi.mock("@/services/api/assistant", () => ({
  getAssistantStatus: vi.fn(),
  streamLogsExplanation: vi.fn(),
}));

const STATUS = { available: true, reason: "", provider: "anthropic", model: "", readOnly: true };

const DIAGNOSIS = {
  source: "solver.log",
  causes: [
    {
      code: "infeasible_problem",
      confidence: "high",
      title: "The optimisation problem has no solution",
      explanation: "",
      suggestion: "",
      evidence: ["[solver][error] Year 12, week 37: infeasible linear problem encountered"],
    },
  ],
  error_lines: ["[solver][error] Year 12, week 37: infeasible linear problem encountered"],
  last_lines: [],
  notes: [],
};

function mockStream() {
  const requests: StreamLogsExplanationParams[] = [];
  const end = deferred<void>();

  vi.mocked(streamLogsExplanation).mockImplementation((params) => {
    requests.push(params);
    return end.promise;
  });

  return {
    requests,
    send: (event: AssistantEvent) => act(() => requests.at(-1)?.onEvent(event)),
    end: () => act(() => end.resolve()),
  };
}

async function openDialog() {
  render(<LogsExplanation studyId="study-1" />, {
    wrapper: createQueryWrapper(createQueryClient()),
  });
  await userEvent.click(await screen.findByRole("button", { name: "study.explainLogs.tooltip" }));
}

describe("LogsExplanation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getAssistantStatus).mockResolvedValue(STATUS);
  });

  test("explains a log file chosen by the user", async () => {
    const stream = mockStream();
    await openDialog();
    expect(screen.getByRole("button", { name: "study.explainLogs.explain" })).toBeDisabled();

    const file = new File(["[solver][error] infeasible\n"], "solver.log", { type: "text/plain" });
    await userEvent.upload(screen.getByTestId("logs-file-input"), file);
    await userEvent.type(screen.getByLabelText("study.explainLogs.solverVersion"), "8.8");
    await userEvent.click(screen.getByRole("button", { name: "study.explainLogs.explain" }));

    expect(stream.requests[0]).toMatchObject({
      studyId: "study-1",
      logs: "[solver][error] infeasible\n",
      fileName: "solver.log",
      solverVersion: "8.8",
    });

    stream.send({ type: "tool_call", name: "diagnose_logs", input: {} });
    expect(screen.getByText("tasks.explain.phase.diagnosing")).toBeInTheDocument();

    stream.send({
      type: "tool_result",
      name: "diagnose_logs",
      is_error: false,
      duration_s: 0.1,
      content: JSON.stringify(DIAGNOSIS),
    });
    stream.send({ type: "done", answer: "The week 37 is **infeasible**.", history: [] });
    await stream.end();

    expect(screen.getByText("The optimisation problem has no solution")).toBeInTheDocument();
    expect(screen.getByText("infeasible")).toBeInTheDocument();

    // Back to the form, with the same logs
    await userEvent.click(screen.getByRole("button", { name: "study.explainLogs.editLogs" }));
    expect(screen.getByText("solver.log")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "study.explainLogs.explain" })).toBeEnabled();
  });

  test("explains pasted logs", async () => {
    const stream = mockStream();
    await openDialog();

    await userEvent.click(screen.getByLabelText("study.explainLogs.logs"));
    await userEvent.paste("[solver][fatal] bad_alloc");
    await userEvent.click(screen.getByRole("button", { name: "study.explainLogs.explain" }));

    expect(stream.requests[0]).toMatchObject({
      logs: "[solver][fatal] bad_alloc",
      fileName: "logs.txt",
      solverVersion: undefined,
    });
  });
});
