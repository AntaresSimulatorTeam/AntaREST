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
  streamCheckSummary,
  streamFindingsExplanation,
  streamStudyCheck,
  streamStudyReview,
} from "@/services/api/assistant";
import { mockAssistantStream } from "@/tests/assistantStream";
import { createQueryClient, createQueryWrapper } from "@/tests/queryUtils";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import StudyCheck from "..";
import { downloadPdf } from "../pdf/downloadPdf";

const { enqueueErrorSnackbar } = vi.hoisted(() => ({ enqueueErrorSnackbar: vi.fn() }));

vi.mock("../pdf/downloadPdf", () => ({ downloadPdf: vi.fn() }));
vi.mock("@/hooks/useEnqueueErrorSnackbar", () => ({ default: () => enqueueErrorSnackbar }));
vi.mock("@/services/api/assistant", () => ({
  getAssistantStatus: vi.fn(),
  streamAssistantChat: vi.fn(),
  streamCheckSummary: vi.fn(),
  streamFindingsExplanation: vi.fn(),
  streamStudyCheck: vi.fn(),
  streamStudyReview: vi.fn(),
}));

const STATUS = { available: true, readOnly: true };

const HYDRO = {
  rule: "hydro_generation_power",
  severity: "error",
  message: "Hydro inflows but no generating power.",
  objects: ["fr", "es"],
  count: 39,
};

const COST_WARNING = {
  rule: "unsupplied_energy_cost",
  severity: "warning",
  message: "Unsupplied energy cost below the most expensive plant.",
  objects: ["de (100 < 180 EUR/MWh)"],
  count: 1,
};

const COST_INFO = {
  rule: "unsupplied_energy_cost",
  severity: "info",
  message: "Unsupplied energy cost of 0.",
  objects: ["x_helper"],
  count: 1,
};

const FINDINGS = [HYDRO, COST_WARNING, COST_INFO];

const REPORT_JSON = JSON.stringify({
  summary: { error: 1, warning: 1, info: 1 },
  findings: FINDINGS,
  rules_run: [],
  rules_skipped: [],
  notes: [],
});

const VERDICT = "The study is **not ready** to be simulated: 1 error to fix or confirm first.";
const THREAD_HISTORY = [{ role: "user", content: "Why is it an error?" }];

/**
 * Opens the panel and runs a check until its findings are shown.
 *
 * @returns The stream of the check, still running.
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
  stream.send({ type: "done", answer: VERDICT, history: [] });
  await stream.end();
}

/**
 * Expands the findings of a rule.
 *
 * @param rule - The rule.
 * @returns Queries limited to the details of the rule.
 */
async function openRule(rule: string) {
  await userEvent.click(screen.getByRole("button", { name: new RegExp(rule) }));
  return within(screen.getByRole("region", { name: new RegExp(rule) }));
}

function renderStudyCheck() {
  return render(<StudyCheck studyId="study-1" studyName="Reference 2030" />, {
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

  test("runs the rules, shows their progress, then the findings and the verdict, without the AI", async () => {
    const stream = mockAssistantStream(streamStudyCheck);
    renderStudyCheck();

    await userEvent.click(await screen.findByRole("button", { name: "study.check.button" }));

    expect(streamStudyCheck).toHaveBeenCalledWith(
      expect.objectContaining({ studyId: "study-1", language: "en" }),
    );
    // The rules start: no percentage can be given yet
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

    stream.send({
      type: "tool_result",
      name: "check_study",
      is_error: false,
      duration_s: 85,
      content: REPORT_JSON,
    });
    stream.send({ type: "done", answer: VERDICT });
    await stream.end();

    expect(screen.getByText("Hydro inflows but no generating power.")).toBeInTheDocument();
    expect(screen.getByText("not ready")).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "study.check.restart" })).toBeInTheDocument();
    // Nothing was asked to the AI model
    expect(streamFindingsExplanation).not.toHaveBeenCalled();
    expect(streamCheckSummary).not.toHaveBeenCalled();
    expect(streamStudyReview).not.toHaveBeenCalled();
  });

  test("shows one block per rule, with all the findings of the rule", async () => {
    await runCheck();

    // Two findings of the same rule: one block, which counts the objects of both
    expect(
      screen.getAllByRole("button", { name: /hydro_generation_power|unsupplied_energy_cost/ }),
    ).toHaveLength(2);
    const rule = await openRule("unsupplied_energy_cost");
    expect(rule.getByText(COST_WARNING.message)).toBeInTheDocument();
    expect(rule.getByText(COST_INFO.message)).toBeInTheDocument();
    expect(
      within(screen.getByRole("button", { name: /unsupplied_energy_cost/ })).getByText("2"),
    ).toBeInTheDocument();
  });

  describe("explanation of a rule", () => {
    test("is asked to the AI only when the user clicks, with the findings of that rule", async () => {
      const explanation = mockAssistantStream(streamFindingsExplanation);
      await runCheck();
      const rule = await openRule("unsupplied_energy_cost");

      await userEvent.click(rule.getByRole("button", { name: "study.check.explain.button" }));

      expect(explanation.requests).toHaveLength(1);
      expect(explanation.requests[0]).toMatchObject({
        studyId: "study-1",
        language: "en",
        findings: [COST_WARNING, COST_INFO],
      });
      expect(rule.getByText("study.check.explain.pending")).toBeInTheDocument();

      explanation.send({ type: "done", answer: "Load is **shed** before the plant runs." });
      await explanation.end();

      expect(rule.getByText("shed")).toBeInTheDocument();
      expect(rule.getByText("study.check.explain.disclaimer")).toBeInTheDocument();
      // The other rule was not explained
      const hydro = await openRule("hydro_generation_power");
      expect(hydro.queryByText("shed")).not.toBeInTheDocument();
      expect(hydro.getByRole("button", { name: "study.check.explain.button" })).toBeInTheDocument();
    });

    test("shows the reason of a failure and lets the user ask again", async () => {
      const explanation = mockAssistantStream(streamFindingsExplanation);
      await runCheck();
      const rule = await openRule("hydro_generation_power");
      await userEvent.click(rule.getByRole("button", { name: "study.check.explain.button" }));

      explanation.send({ type: "error", message: "The model server rejected the API key." });
      await explanation.end();

      // The findings of the rules do not depend on the model: they are still there
      expect(rule.getByText("The model server rejected the API key.")).toBeInTheDocument();
      expect(rule.getByText(HYDRO.message)).toBeInTheDocument();

      await userEvent.click(rule.getByRole("button", { name: "study.check.explain.button" }));

      expect(explanation.requests).toHaveLength(2);
    });

    test("is forgotten when the check is run again", async () => {
      const explanation = mockAssistantStream(streamFindingsExplanation);
      await runCheck();
      const rule = await openRule("hydro_generation_power");
      await userEvent.click(rule.getByRole("button", { name: "study.check.explain.button" }));
      explanation.send({ type: "done", answer: "No turbine can run." });
      await explanation.end();

      await userEvent.click(screen.getByRole("button", { name: "study.check.restart" }));

      expect(screen.queryByText("No turbine can run.")).not.toBeInTheDocument();
    });
  });

  describe("summary and review", () => {
    test("the summary of all the findings is written on request", async () => {
      const summary = mockAssistantStream(streamCheckSummary);
      await runCheck();

      await userEvent.click(screen.getByRole("button", { name: "study.check.summary.button" }));

      expect(summary.requests[0]).toMatchObject({ studyId: "study-1", findings: FINDINGS });
      expect(screen.getByText("study.check.summary.pending")).toBeInTheDocument();

      summary.send({ type: "done", answer: "Fix the **hydro** power first." });
      await summary.end();

      expect(screen.getByText("hydro")).toBeInTheDocument();
      expect(screen.getByText("study.check.summary.disclaimer")).toBeInTheDocument();
    });

    test("no summary is offered without error nor warning", async () => {
      const stream = mockAssistantStream(streamStudyCheck);
      renderStudyCheck();
      await userEvent.click(await screen.findByRole("button", { name: "study.check.button" }));
      stream.send({
        type: "tool_result",
        name: "check_study",
        is_error: false,
        duration_s: 1,
        content: JSON.stringify({
          summary: { error: 0, warning: 0, info: 1 },
          findings: [COST_INFO],
          notes: [],
        }),
      });
      stream.send({ type: "done", answer: "The study can be simulated." });
      await stream.end();

      expect(screen.getByText("The study can be simulated.")).toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: "study.check.summary.button" }),
      ).not.toBeInTheDocument();
      expect(screen.getByRole("button", { name: "study.check.review.button" })).toBeInTheDocument();
    });

    test("the review is told the findings of the rules, not to repeat them", async () => {
      const review = mockAssistantStream(streamStudyReview);
      await runCheck();

      await userEvent.click(screen.getByRole("button", { name: "study.check.review.button" }));
      review.send({ type: "tool_call", name: "survey_study", input: {} });

      expect(review.requests[0]).toMatchObject({ studyId: "study-1", findings: FINDINGS });

      review.send({ type: "done", answer: "A capacity of **9,000,000 MW** is surprising." });
      await review.end();

      expect(screen.getByText("9,000,000 MW")).toBeInTheDocument();
      expect(screen.getByText("study.check.review.disclaimer")).toBeInTheDocument();
    });
  });

  test("shows the error of the check and lets the user retry", async () => {
    const stream = mockAssistantStream(streamStudyCheck);
    renderStudyCheck();
    await userEvent.click(await screen.findByRole("button", { name: "study.check.button" }));

    stream.send({ type: "error", message: "The rules could not be run on this study." });
    await stream.end();

    expect(screen.getByText("The rules could not be run on this study.")).toBeInTheDocument();

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

  describe("PDF report", () => {
    beforeEach(() => {
      vi.mocked(downloadPdf).mockResolvedValue(undefined);
    });

    async function downloadReport() {
      await userEvent.click(screen.getByRole("button", { name: "study.check.pdf.button" }));
      await waitFor(() => expect(downloadPdf).toHaveBeenCalledOnce());
      const [definition, fileName] = vi.mocked(downloadPdf).mock.calls[0];
      return { text: JSON.stringify(definition.content), fileName };
    }

    test("the verdict and the findings are downloaded as a PDF named after the study", async () => {
      await runCheck();

      const { text, fileName } = await downloadReport();

      expect(fileName).toBe("study.check.pdf.fileName.pdf");
      expect(text).toContain("Reference 2030");
      expect(text).toContain("not ready");
      expect(text).toContain(HYDRO.message);
      expect(text).toContain(COST_INFO.message);
    });

    test("the report has the texts the assistant has written", async () => {
      const summary = mockAssistantStream(streamCheckSummary);
      await runCheck();
      await userEvent.click(screen.getByRole("button", { name: "study.check.summary.button" }));
      summary.send({ type: "done", answer: "Fix the hydro power first." });
      await summary.end();

      const { text } = await downloadReport();

      expect(text).toContain("study.check.summary.title");
      expect(text).toContain("Fix the hydro power first.");
    });

    test("the report has the explanation of a rule the user asked for", async () => {
      const explanation = mockAssistantStream(streamFindingsExplanation);
      await runCheck();
      const rule = await openRule("unsupplied_energy_cost");
      await userEvent.click(rule.getByRole("button", { name: "study.check.explain.button" }));
      explanation.send({ type: "done", answer: "Load is shed before the plant runs." });
      await explanation.end();

      const { text } = await downloadReport();

      expect(text).toContain("study.check.pdf.explanation");
      expect(text).toContain("Load is shed before the plant runs.");
    });

    test("the report leaves out a text the assistant is still writing", async () => {
      mockAssistantStream(streamCheckSummary);
      await runCheck();
      await userEvent.click(screen.getByRole("button", { name: "study.check.summary.button" }));

      const { text } = await downloadReport();

      expect(text).not.toContain("study.check.summary.title");
    });

    test("no report is offered before the end of the check", async () => {
      await runRules();

      expect(
        screen.queryByRole("button", { name: "study.check.pdf.button" }),
      ).not.toBeInTheDocument();
    });

    test("the user is told when the report cannot be generated, and can try again", async () => {
      const failure = new Error("The fonts could not be loaded.");
      vi.mocked(downloadPdf).mockRejectedValue(failure);
      await runCheck();

      await userEvent.click(screen.getByRole("button", { name: "study.check.pdf.button" }));

      await waitFor(() =>
        expect(enqueueErrorSnackbar).toHaveBeenCalledWith("study.check.pdf.failed", failure),
      );
      expect(screen.getByRole("button", { name: "study.check.pdf.button" })).toBeEnabled();
    });
  });

  describe("conversation about a rule", () => {
    test("starts with the findings of the rule and the question of the user", async () => {
      const chat = mockAssistantStream(streamAssistantChat);
      await runCheck();
      const finding = await openRule("hydro_generation_power");

      await userEvent.type(finding.getByRole("textbox"), "Why is it an error?{Enter}");

      expect(chat.requests[0]).toMatchObject({ studyId: "study-1", history: [] });
      // The assistant is told which findings the user is looking at
      expect(chat.requests[0].message).toContain("rule `hydro_generation_power`");
      expect(chat.requests[0].message).toContain(HYDRO.message);
      expect(chat.requests[0].message).toContain("Why is it an error?");
      // The user sees their own words only
      expect(finding.getByText("Why is it an error?")).toBeInTheDocument();

      chat.send({ type: "tool_call", name: "get_matrix_stats", input: { path: "hydro" } });
      expect(finding.getByText("get_matrix_stats(path=hydro)")).toBeInTheDocument();
      chat.send({ type: "done", answer: "No **turbine** can run.", history: THREAD_HISTORY });
      await chat.end();

      expect(finding.getByText("turbine")).toBeInTheDocument();
    });

    test("is separate for each rule", async () => {
      const chat = mockAssistantStream(streamAssistantChat);
      await runCheck();
      const hydro = await openRule("hydro_generation_power");
      await userEvent.type(hydro.getByRole("textbox"), "Why is it an error?{Enter}");
      chat.send({ type: "done", answer: "No turbine can run.", history: THREAD_HISTORY });
      await chat.end();

      const cost = await openRule("unsupplied_energy_cost");
      await userEvent.type(cost.getByRole("textbox"), "Is it a problem?{Enter}");

      // The second conversation does not continue the first one
      expect(chat.requests[1].history).toEqual([]);
      expect(chat.requests[1].message).toContain("rule `unsupplied_energy_cost`");
      expect(cost.queryByText("No turbine can run.")).not.toBeInTheDocument();
    });

    test("tells that a read-only assistant cannot correct the study", async () => {
      await runCheck();

      const finding = await openRule("hydro_generation_power");

      expect(
        finding.getByRole("textbox", { name: "study.check.finding.askReadOnly" }),
      ).toBeEnabled();
      expect(finding.getByText("study.check.finding.readOnlyHint")).toBeInTheDocument();
    });

    test("offers to run the check again after a correction by the assistant", async () => {
      vi.mocked(getAssistantStatus).mockResolvedValue({ ...STATUS, readOnly: false });
      const chat = mockAssistantStream(streamAssistantChat);
      await runCheck();
      const finding = await openRule("hydro_generation_power");

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
      const finding = await openRule("hydro_generation_power");
      await userEvent.type(finding.getByRole("textbox"), "Why is it an error?{Enter}");
      chat.send({ type: "done", answer: "No turbine can run.", history: THREAD_HISTORY });
      await chat.end();

      await userEvent.click(screen.getByRole("button", { name: "global.close" }));
      await waitFor(() => expect(screen.queryByText("not ready")).not.toBeInTheDocument());
      // The button shows the number of findings to look at (1 error + 1 warning)
      expect(screen.getByText("2")).toBeInTheDocument();
      await userEvent.click(screen.getByRole("button", { name: "study.check.button" }));

      expect(screen.getByText("not ready")).toBeInTheDocument();
      expect(screen.getByText("No turbine can run.")).toBeInTheDocument();
      expect(streamStudyCheck).toHaveBeenCalledTimes(1);
    });

    test("is forgotten when the check is run again", async () => {
      const chat = mockAssistantStream(streamAssistantChat);
      await runCheck();
      const finding = await openRule("hydro_generation_power");
      await userEvent.type(finding.getByRole("textbox"), "Why is it an error?{Enter}");
      chat.send({ type: "done", answer: "No turbine can run.", history: THREAD_HISTORY });
      await chat.end();

      await userEvent.click(screen.getByRole("button", { name: "study.check.restart" }));

      expect(screen.queryByText("No turbine can run.")).not.toBeInTheDocument();
    });
  });
});
