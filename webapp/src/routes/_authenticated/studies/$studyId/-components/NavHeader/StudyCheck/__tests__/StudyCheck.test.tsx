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

import {
  getAssistantStatus,
  streamAssistantChat,
  streamStudyCheck,
} from "@/services/api/assistant";
import type {
  AssistantEvent,
  StreamAssistantChatParams,
  StreamStudyCheckParams,
} from "@/services/api/assistant/types";
import { createQueryClient, createQueryWrapper, deferred } from "@/tests/queryUtils";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import StudyCheck from "..";

vi.mock("@/services/api/assistant", () => ({
  getAssistantStatus: vi.fn(),
  streamAssistantChat: vi.fn(),
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

const CHECK_HISTORY = [{ role: "user", content: "Check this study" }];
const THREAD_HISTORY = [...CHECK_HISTORY, { role: "user", content: "Why is it an error?" }];

/**
 * Replaces the stream of the conversations: each message sent gets its own controllable stream.
 *
 * @returns The received requests, and functions to send an event to the last one and to end it.
 */
function mockChat() {
  const requests: StreamAssistantChatParams[] = [];
  let end = deferred<void>();

  vi.mocked(streamAssistantChat).mockImplementation((params) => {
    requests.push(params);
    end = deferred<void>();
    return end.promise;
  });

  return {
    requests,
    send: (event: AssistantEvent) => act(() => requests.at(-1)?.onEvent(event)),
    end: () =>
      act(async () => {
        end.resolve();
        await end.promise;
      }),
  };
}

/**
 * Opens the panel and runs a check until its two findings are shown.
 *
 * @returns The stream of the check, still running: the assistant has not written its analysis.
 */
async function runRules() {
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
  return stream;
}

async function runCheck() {
  const stream = await runRules();
  stream.send({ type: "done", answer: "Done.", history: CHECK_HISTORY });
  stream.end();
}

/**
 * Expands a finding.
 *
 * @param rule - Rule of the finding.
 * @returns Queries limited to the details of the finding.
 */
async function openFinding(rule: string) {
  await userEvent.click(screen.getByRole("button", { name: new RegExp(rule) }));
  return within(screen.getByRole("region", { name: new RegExp(rule) }));
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

  describe("conversation about a finding", () => {
    test("continues the conversation of the check with the question of the user", async () => {
      const chat = mockChat();
      await runCheck();
      const finding = await openFinding("hydro_generation_power");

      await userEvent.type(finding.getByRole("textbox"), "Why is it an error?{Enter}");

      expect(chat.requests[0]).toMatchObject({ studyId: "study-1", history: CHECK_HISTORY });
      // The assistant is told which finding the user is looking at
      expect(chat.requests[0].message).toContain("hydro_generation_power (error)");
      expect(chat.requests[0].message).toContain("Why is it an error?");
      // The user sees their own words only
      expect(finding.getByText("Why is it an error?")).toBeInTheDocument();

      chat.send({ type: "tool_call", name: "get_matrix_stats", input: { path: "hydro" } });
      expect(finding.getByText("get_matrix_stats(path=hydro)")).toBeInTheDocument();
      chat.send({ type: "done", answer: "No **turbine** can run.", history: THREAD_HISTORY });
      await chat.end();

      expect(finding.getByText("turbine")).toBeInTheDocument();

      await userEvent.type(finding.getByRole("textbox"), "How to fix it?{Enter}");

      expect(chat.requests[1]).toMatchObject({
        history: THREAD_HISTORY,
        message: "How to fix it?",
      });
    });

    test("is separate for each finding", async () => {
      const chat = mockChat();
      await runCheck();
      const hydro = await openFinding("hydro_generation_power");
      await userEvent.type(hydro.getByRole("textbox"), "Why is it an error?{Enter}");
      chat.send({ type: "done", answer: "No turbine can run.", history: THREAD_HISTORY });
      await chat.end();

      const calendar = await openFinding("calendar");
      await userEvent.type(calendar.getByRole("textbox"), "Is it a problem?{Enter}");

      // The second conversation starts from the check, not from the first conversation
      expect(chat.requests[1].history).toEqual(CHECK_HISTORY);
      expect(chat.requests[1].message).toContain("calendar (warning)");
      expect(calendar.queryByText("No turbine can run.")).not.toBeInTheDocument();
    });

    test("waits for the end of the check", async () => {
      await runRules();

      const finding = await openFinding("hydro_generation_power");

      expect(finding.getByRole("textbox")).toBeDisabled();
      expect(finding.getByText("study.check.finding.waitForCheck")).toBeInTheDocument();
    });

    test("tells that a read-only assistant cannot correct the study", async () => {
      await runCheck();

      const finding = await openFinding("hydro_generation_power");

      expect(
        finding.getByRole("textbox", { name: "study.check.finding.askReadOnly" }),
      ).toBeEnabled();
      expect(finding.getByText("study.check.finding.readOnlyHint")).toBeInTheDocument();
    });

    test("offers to run the check again after a correction by the assistant", async () => {
      vi.mocked(getAssistantStatus).mockResolvedValue({ ...STATUS, readOnly: false });
      const chat = mockChat();
      await runCheck();
      const finding = await openFinding("hydro_generation_power");

      await userEvent.type(
        finding.getByRole("textbox", { name: "study.check.finding.ask" }),
        "Fix it{Enter}",
      );
      chat.send({ type: "tool_call", name: "update_thermal_cluster", input: {} });
      chat.send({ type: "done", answer: "Fixed.", history: THREAD_HISTORY });
      await chat.end();

      expect(screen.getByText("study.check.outdated")).toBeInTheDocument();
    });

    test("is kept when the panel is closed and reopened", async () => {
      const chat = mockChat();
      await runCheck();
      const finding = await openFinding("hydro_generation_power");
      await userEvent.type(finding.getByRole("textbox"), "Why is it an error?{Enter}");
      chat.send({ type: "done", answer: "No turbine can run.", history: THREAD_HISTORY });
      await chat.end();

      await userEvent.click(screen.getByRole("button", { name: "global.close" }));
      await waitFor(() => expect(screen.queryByText("Done.")).not.toBeInTheDocument());
      await userEvent.click(screen.getByRole("button", { name: "study.check.button" }));

      expect(screen.getByText("No turbine can run.")).toBeInTheDocument();
    });

    test("is forgotten when the check is run again", async () => {
      const chat = mockChat();
      await runCheck();
      const finding = await openFinding("hydro_generation_power");
      await userEvent.type(finding.getByRole("textbox"), "Why is it an error?{Enter}");
      chat.send({ type: "done", answer: "No turbine can run.", history: THREAD_HISTORY });
      await chat.end();

      await userEvent.click(screen.getByRole("button", { name: "study.check.restart" }));

      expect(screen.queryByText("No turbine can run.")).not.toBeInTheDocument();
    });
  });
});
