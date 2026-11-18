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
  streamJobExplanation,
} from "@/services/api/assistant";
import type { AssistantEvent } from "@/services/api/assistant/types";
import { mockAssistantStream } from "@/tests/assistantStream";
import { createQueryClient, createQueryWrapper } from "@/tests/queryUtils";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import JobFailureExplanation from "..";
import { INITIAL_EXPLANATION_STATE, parseJobDiagnosis, reduceExplanationEvent } from "../utils";

vi.mock("@/services/api/assistant", () => ({
  getAssistantStatus: vi.fn(),
  streamAssistantChat: vi.fn(),
  streamJobExplanation: vi.fn(),
}));

const STATUS = { available: true, readOnly: true };
const ERROR_LINE = "[solver][fatal] The folder `/tmp/x` does not seem to be a valid study";

const DIAGNOSIS_JSON = JSON.stringify({
  job: { id: "job-1", study_id: "study-1", status: "failed" },
  causes: [
    {
      code: "solver_version_mismatch",
      confidence: "high",
      title: "The solver cannot read this study version",
      explanation: "The solver rejected the study as invalid.",
      suggestion: "Launch again with a more recent solver.",
      evidence: [ERROR_LINE],
    },
  ],
  error_lines: [ERROR_LINE],
  last_lines: [],
  notes: [],
});

const DIAGNOSE_CALL: AssistantEvent = { type: "tool_call", name: "diagnose_job", input: {} };
const DIAGNOSE_RESULT: AssistantEvent = {
  type: "tool_result",
  name: "diagnose_job",
  is_error: false,
  duration_s: 0.2,
  content: DIAGNOSIS_JSON,
};

const EXPLANATION_HISTORY = [{ role: "user", content: "Why did the job fail?" }];
const THREAD_HISTORY = [...EXPLANATION_HISTORY, { role: "user", content: "Which solver?" }];
const ASK = "tasks.explain.ask";

/** Opens the dialog and runs an explanation to its end. */
async function explain() {
  const stream = mockAssistantStream(streamJobExplanation);
  renderExplanation();
  await userEvent.click(await screen.findByRole("button", { name: "tasks.explain.button" }));
  stream.send(DIAGNOSE_CALL);
  stream.send(DIAGNOSE_RESULT);
  stream.send({ type: "done", answer: "The solver is too old.", history: EXPLANATION_HISTORY });
  await stream.end();
}

function renderExplanation() {
  return render(<JobFailureExplanation jobId="job-1" />, {
    wrapper: createQueryWrapper(createQueryClient()),
  });
}

describe("reduceExplanationEvent", () => {
  test("keeps the reason when the job could not be read", () => {
    const state = reduceExplanationEvent(INITIAL_EXPLANATION_STATE, {
      ...DIAGNOSE_RESULT,
      is_error: true,
      content: "Antares Web returned HTTP 404: job not found",
    });

    expect(state.diagnosis).toBeUndefined();
    expect(state.diagnosisError).toBe("Antares Web returned HTTP 404: job not found");
  });

  test("parseJobDiagnosis rejects what is not a diagnosis", () => {
    expect(parseJobDiagnosis(undefined)).toBeUndefined();
    expect(parseJobDiagnosis("Error executing tool")).toBeUndefined();
    expect(parseJobDiagnosis('{"causes": "none"}')).toBeUndefined();
  });
});

describe("JobFailureExplanation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getAssistantStatus).mockResolvedValue(STATUS);
  });

  test("is hidden when the server has no assistant", async () => {
    vi.mocked(getAssistantStatus).mockResolvedValue({ ...STATUS, available: false });

    renderExplanation();

    await waitFor(() => expect(getAssistantStatus).toHaveBeenCalled());
    expect(screen.queryByRole("button", { name: "tasks.explain.button" })).not.toBeInTheDocument();
  });

  test("shows the probable causes, then the explanation of the assistant", async () => {
    const stream = mockAssistantStream(streamJobExplanation);
    renderExplanation();

    await userEvent.click(await screen.findByRole("button", { name: "tasks.explain.button" }));

    expect(streamJobExplanation).toHaveBeenCalledWith(
      expect.objectContaining({ jobId: "job-1", language: "en" }),
    );
    expect(screen.getByText("tasks.explain.phase.starting")).toBeInTheDocument();

    stream.send(DIAGNOSE_CALL);
    expect(screen.getByText("tasks.explain.phase.diagnosing")).toBeInTheDocument();

    // The causes found by the rules are shown while the assistant writes
    stream.send(DIAGNOSE_RESULT);
    expect(screen.getByText("The solver cannot read this study version")).toBeInTheDocument();
    expect(screen.getByText("tasks.explain.confidence.high")).toBeInTheDocument();
    expect(screen.getAllByText(ERROR_LINE)).toHaveLength(2); // evidence of the cause + error lines
    expect(screen.getByText("tasks.explain.writing")).toBeInTheDocument();
    stream.send({ type: "tool_call", name: "get_job_logs", input: {} });
    expect(screen.getByText("tasks.explain.digging")).toBeInTheDocument();

    stream.send({ type: "done", answer: "The solver **8.8** cannot read a 9.2 study." });
    await stream.end();

    expect(screen.getByText("8.8")).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "tasks.explain.restart" })).toBeInTheDocument();
  });

  test("shows the advice of the rules when the assistant fails", async () => {
    const stream = mockAssistantStream(streamJobExplanation);
    renderExplanation();
    await userEvent.click(await screen.findByRole("button", { name: "tasks.explain.button" }));

    stream.send(DIAGNOSE_RESULT);
    stream.send({ type: "error", message: "The rate limit of the model server is reached." });
    await stream.end();

    expect(screen.getByText("The rate limit of the model server is reached.")).toBeInTheDocument();
    // Without the explanation of the assistant, the explanation of the rule is the fallback
    expect(screen.getByText(/Launch again with a more recent solver/)).toBeInTheDocument();
  });

  describe("questions about the cause", () => {
    test("continue the conversation of the explanation", async () => {
      const chat = mockAssistantStream(streamAssistantChat);
      await explain();

      await userEvent.type(screen.getByRole("textbox", { name: ASK }), "Which solver?{Enter}");

      expect(chat.requests[0]).toMatchObject({ history: EXPLANATION_HISTORY });
      // The assistant is told which job the question is about
      expect(chat.requests[0].message).toContain("job-1");
      expect(chat.requests[0].message).toContain("Which solver?");
      // The user sees their own words only
      expect(screen.getByText("Which solver?")).toBeInTheDocument();

      chat.send({ type: "tool_call", name: "list_launchers", input: {} });
      expect(screen.getByText("list_launchers()")).toBeInTheDocument();
      chat.send({ type: "done", answer: "Use the solver **10.2**.", history: THREAD_HISTORY });
      await chat.end();

      expect(screen.getByText("10.2")).toBeInTheDocument();
    });

    test("are offered only once the assistant has explained", async () => {
      const stream = mockAssistantStream(streamJobExplanation);
      renderExplanation();
      await userEvent.click(await screen.findByRole("button", { name: "tasks.explain.button" }));

      stream.send(DIAGNOSE_RESULT);
      expect(screen.queryByRole("textbox", { name: ASK })).not.toBeInTheDocument();

      stream.send({ type: "error", message: "The rate limit of the model server is reached." });
      await stream.end();
      expect(screen.queryByRole("textbox", { name: ASK })).not.toBeInTheDocument();
    });

    test("are kept when the dialog is closed and reopened", async () => {
      const chat = mockAssistantStream(streamAssistantChat);
      await explain();
      await userEvent.type(screen.getByRole("textbox", { name: ASK }), "Which solver?{Enter}");
      chat.send({ type: "done", answer: "Use the solver 10.2.", history: THREAD_HISTORY });
      await chat.end();

      await userEvent.click(screen.getByRole("button", { name: "global.close" }));
      await waitFor(() =>
        expect(screen.queryByText("Use the solver 10.2.")).not.toBeInTheDocument(),
      );
      await userEvent.click(screen.getByRole("button", { name: "tasks.explain.button" }));

      expect(screen.getByText("Use the solver 10.2.")).toBeInTheDocument();
    });

    test("are forgotten when the explanation is run again", async () => {
      const chat = mockAssistantStream(streamAssistantChat);
      await explain();
      await userEvent.type(screen.getByRole("textbox", { name: ASK }), "Which solver?{Enter}");
      chat.send({ type: "done", answer: "Use the solver 10.2.", history: THREAD_HISTORY });
      await chat.end();

      await userEvent.click(screen.getByRole("button", { name: "tasks.explain.restart" }));

      expect(screen.queryByText("Use the solver 10.2.")).not.toBeInTheDocument();
    });
  });
});
