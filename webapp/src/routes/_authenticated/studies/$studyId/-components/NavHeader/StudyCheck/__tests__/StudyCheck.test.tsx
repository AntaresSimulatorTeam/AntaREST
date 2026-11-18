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
import { mockAssistantStream } from "@/tests/assistantStream";
import { createQueryClient, createQueryWrapper } from "@/tests/queryUtils";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import StudyCheck from "..";

vi.mock("@/services/api/assistant", () => ({
  getAssistantStatus: vi.fn(),
  streamAssistantChat: vi.fn(),
  streamStudyCheck: vi.fn(),
}));

const STATUS = { available: true, readOnly: true };

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

const CHECK_HISTORY = [{ role: "user", content: "Check this study" }];
const THREAD_HISTORY = [...CHECK_HISTORY, { role: "user", content: "Why is it an error?" }];

/**
 * Opens the panel and runs a check until its two findings are shown.
 *
 * @returns The stream of the check, still running: the assistant has not written its analysis.
 */
async function runRules() {
  const stream = mockAssistantStream(streamStudyCheck);
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
  await stream.end();
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
    const stream = mockAssistantStream(streamStudyCheck);
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
    await stream.end();

    expect(screen.getByText("not ready")).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "study.check.restart" })).toBeInTheDocument();
  });

  test("shows the error of the assistant and lets the user retry", async () => {
    const stream = mockAssistantStream(streamStudyCheck);
    renderStudyCheck();
    await userEvent.click(await screen.findByRole("button", { name: "study.check.button" }));

    stream.send({ type: "error", message: "The model server rejected the API key." });
    await stream.end();

    expect(screen.getByText("The model server rejected the API key.")).toBeInTheDocument();

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
    const stream = mockAssistantStream(streamStudyCheck);
    renderStudyCheck();
    await userEvent.click(await screen.findByRole("button", { name: "study.check.button" }));

    await userEvent.click(screen.getByRole("button", { name: "global.cancel" }));

    expect(stream.requests[0].signal.aborted).toBe(true);
    await waitFor(() => expect(screen.queryByRole("progressbar")).not.toBeInTheDocument());
  });

  describe("conversation about a finding", () => {
    test("continues the conversation of the check with the question of the user", async () => {
      const chat = mockAssistantStream(streamAssistantChat);
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
    });

    test("is separate for each finding", async () => {
      const chat = mockAssistantStream(streamAssistantChat);
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
      const chat = mockAssistantStream(streamAssistantChat);
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

    test("is kept, with the result of the check, when the panel is closed and reopened", async () => {
      const chat = mockAssistantStream(streamAssistantChat);
      await runCheck();
      const finding = await openFinding("hydro_generation_power");
      await userEvent.type(finding.getByRole("textbox"), "Why is it an error?{Enter}");
      chat.send({ type: "done", answer: "No turbine can run.", history: THREAD_HISTORY });
      await chat.end();

      await userEvent.click(screen.getByRole("button", { name: "global.close" }));
      await waitFor(() => expect(screen.queryByText("Done.")).not.toBeInTheDocument());
      // The button shows the number of findings to look at (1 error + 1 warning)
      expect(screen.getByText("2")).toBeInTheDocument();
      await userEvent.click(screen.getByRole("button", { name: "study.check.button" }));

      expect(screen.getByText("Done.")).toBeInTheDocument();
      expect(screen.getByText("No turbine can run.")).toBeInTheDocument();
      expect(streamStudyCheck).toHaveBeenCalledTimes(1);
    });

    test("is forgotten when the check is run again", async () => {
      const chat = mockAssistantStream(streamAssistantChat);
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
