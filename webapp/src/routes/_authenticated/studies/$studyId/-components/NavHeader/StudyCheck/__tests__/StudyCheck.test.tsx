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

import { getAssistantStatus, streamStudyCheck } from "@/services/api/assistant";
import type { AssistantEvent, StreamStudyCheckParams } from "@/services/api/assistant/types";
import { createQueryClient, createQueryWrapper, deferred } from "@/tests/queryUtils";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import StudyCheck from "..";

vi.mock("@/services/api/assistant", () => ({
  getAssistantStatus: vi.fn(),
  streamStudyCheck: vi.fn(),
}));

const STATUS = { available: true, reason: "", provider: "anthropic", model: "", readOnly: true };

const REPORT_JSON = JSON.stringify({
  summary: { error: 1, warning: 1, info: 0 },
  findings: [
    {
      rule: "hydro_generation_power",
      severity: "error",
      message: "Hydro inflows but no generating power.",
      objects: ["fr", "es"],
      count: 39,
    },
    {
      rule: "calendar",
      severity: "warning",
      message: "The study uses the 2029 calendar.",
      objects: ["settings/generaldata.ini"],
      count: 1,
    },
  ],
  rules_run: [],
  rules_skipped: [],
  notes: [],
});

/**
 * Replaces the stream of the server: the test sends the events one by one, then ends the stream.
 *
 * @returns Functions to send an event and to end the stream.
 */
function mockStream() {
  const end = deferred<void>();
  let onEvent: StreamStudyCheckParams["onEvent"] | undefined;
  let signal: AbortSignal | undefined;

  vi.mocked(streamStudyCheck).mockImplementation((params) => {
    onEvent = params.onEvent;
    signal = params.signal;
    return end.promise;
  });

  return {
    send: (event: AssistantEvent) => act(() => onEvent?.(event)),
    end: () => act(() => end.resolve()),
    isAborted: () => signal?.aborted,
  };
}

function renderStudyCheck() {
  return render(<StudyCheck studyId="study-1" />, {
    wrapper: createQueryWrapper(createQueryClient()),
  });
}

describe("StudyCheck", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getAssistantStatus).mockResolvedValue(STATUS);
  });

  test("is hidden when the server has no assistant", async () => {
    vi.mocked(getAssistantStatus).mockResolvedValue({ ...STATUS, available: false });

    renderStudyCheck();

    await waitFor(() => expect(getAssistantStatus).toHaveBeenCalled());
    expect(screen.queryByRole("button", { name: "study.check.button" })).not.toBeInTheDocument();
  });

  test("runs the check, shows its progress, then the findings and the analysis", async () => {
    const stream = mockStream();
    renderStudyCheck();

    await userEvent.click(await screen.findByRole("button", { name: "study.check.button" }));

    expect(streamStudyCheck).toHaveBeenCalledWith(
      expect.objectContaining({ studyId: "study-1", language: "en" }),
    );
    // The assistant starts: no percentage can be given yet
    expect(screen.getByText("study.check.phase.starting")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).not.toHaveAttribute("aria-valuenow");

    // The rules run: the progress is known
    stream.send({ type: "tool_call", name: "check_study", input: { deep: true } });
    stream.send({
      type: "tool_progress",
      name: "check_study",
      progress: 2,
      total: 5,
      message: "Checking thermal_availability",
    });
    expect(screen.getByText("study.check.phase.checking")).toBeInTheDocument();
    expect(screen.getByText(/40 %/)).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "40");

    // The findings are shown while the assistant writes its analysis
    stream.send({
      type: "tool_result",
      name: "check_study",
      is_error: false,
      duration_s: 85,
      content: REPORT_JSON,
    });
    expect(screen.getByText("study.check.phase.reporting")).toBeInTheDocument();
    expect(screen.getByText("Hydro inflows but no generating power.")).toBeInTheDocument();
    expect(screen.getByText("The study uses the 2029 calendar.")).toBeInTheDocument();
    expect(screen.getByText("study.check.analysisPending")).toBeInTheDocument();

    stream.send({ type: "done", answer: "The study is **not ready**: fix the hydro power." });
    stream.end();

    expect(screen.getByText("not ready")).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "study.check.restart" })).toBeInTheDocument();
  });

  test("keeps the result after the panel is closed and reopened", async () => {
    const stream = mockStream();
    renderStudyCheck();
    await userEvent.click(await screen.findByRole("button", { name: "study.check.button" }));
    stream.send({ type: "tool_call", name: "check_study", input: {} });
    stream.send({
      type: "tool_result",
      name: "check_study",
      is_error: false,
      duration_s: 1,
      content: REPORT_JSON,
    });
    stream.send({ type: "done", answer: "Done." });
    stream.end();

    await userEvent.click(screen.getByRole("button", { name: "global.close" }));
    await waitFor(() => expect(screen.queryByText("Done.")).not.toBeInTheDocument());
    // The button shows the number of findings to look at (1 error + 1 warning)
    expect(screen.getByText("2")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "study.check.button" }));

    expect(screen.getByText("Done.")).toBeInTheDocument();
    expect(streamStudyCheck).toHaveBeenCalledTimes(1);
  });

  test("shows the error of the assistant and lets the user retry", async () => {
    const stream = mockStream();
    renderStudyCheck();
    await userEvent.click(await screen.findByRole("button", { name: "study.check.button" }));

    stream.send({ type: "error", message: "The Anthropic API key is invalid or revoked." });
    stream.end();

    expect(screen.getByText("The Anthropic API key is invalid or revoked.")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "study.check.restart" }));

    expect(streamStudyCheck).toHaveBeenCalledTimes(2);
  });

  test("shows the reason when the request is rejected", async () => {
    vi.mocked(streamStudyCheck).mockRejectedValue(new Error("No API key for the assistant"));
    renderStudyCheck();

    await userEvent.click(await screen.findByRole("button", { name: "study.check.button" }));

    expect(await screen.findByText("No API key for the assistant")).toBeInTheDocument();
  });

  test("cancels a running check", async () => {
    const stream = mockStream();
    renderStudyCheck();
    await userEvent.click(await screen.findByRole("button", { name: "study.check.button" }));

    await userEvent.click(screen.getByRole("button", { name: "global.cancel" }));

    expect(stream.isAborted()).toBe(true);
    await waitFor(() => expect(screen.queryByRole("progressbar")).not.toBeInTheDocument());
  });
});
