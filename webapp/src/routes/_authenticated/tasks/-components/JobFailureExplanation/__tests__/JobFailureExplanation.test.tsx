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
import type {
  AssistantEvent,
  StreamAssistantChatParams,
  StreamJobExplanationParams,
} from "@/services/api/assistant/types";
import { createQueryClient, createQueryWrapper, deferred } from "@/tests/queryUtils";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import JobFailureExplanation from "..";
import { parseJobDiagnosis, reduceExplanationEvent, RUNNING_EXPLANATION_STATE } from "../utils";

vi.mock("@/services/api/assistant", () => ({
  getAssistantStatus: vi.fn(),
  streamAssistantChat: vi.fn(),
  streamJobExplanation: vi.fn(),
}));

const STATUS = { available: true, reason: "", provider: "anthropic", model: "", readOnly: true };
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

/**
 * Replaces the stream of the server: the test sends the events one by one, then ends the stream.
 *
 * @returns Functions to send an event and to end the stream.
 */
function mockStream() {
  const end = deferred<void>();
  let onEvent: StreamJobExplanationParams["onEvent"] | undefined;

  vi.mocked(streamJobExplanation).mockImplementation((params) => {
    onEvent = params.onEvent;
    return end.promise;
  });

  return {
    send: (event: AssistantEvent) => act(() => onEvent?.(event)),
    end: () => act(() => end.resolve()),
  };
}

const EXPLANATION_HISTORY = [{ role: "user", content: "Why did the job fail?" }];
const THREAD_HISTORY = [...EXPLANATION_HISTORY, { role: "user", content: "Which solver?" }];
const ASK = "tasks.explain.ask";

/**
 * Replaces the stream of the conversation: each message sent gets its own controllable stream.
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

/** Opens the dialog and runs an explanation to its end. */
async function explain() {
  const stream = mockStream();
  renderExplanation();
  await userEvent.click(await screen.findByRole("button", { name: "tasks.explain.button" }));
  stream.send(DIAGNOSE_CALL);
  stream.send(DIAGNOSE_RESULT);
  stream.send({ type: "done", answer: "The solver is too old.", history: EXPLANATION_HISTORY });
  stream.end();
}

function renderExplanation() {
  return render(<JobFailureExplanation jobId="job-1" />, {
    wrapper: createQueryWrapper(createQueryClient()),
  });
}

describe("reduceExplanationEvent", () => {
  test("follows an explanation: diagnosis, digging, answer", () => {
    const diagnosing = reduceExplanationEvent(RUNNING_EXPLANATION_STATE, DIAGNOSE_CALL);
    expect(diagnosing.phase).toBe("diagnosing");

    const explaining = reduceExplanationEvent(diagnosing, DIAGNOSE_RESULT);
    expect(explaining.phase).toBe("explaining");
    expect(explaining.diagnosis?.causes[0].code).toBe("solver_version_mismatch");
    expect(explaining.diagnosis?.errorLines).toEqual([ERROR_LINE]);

    const digging = reduceExplanationEvent(explaining, {
      type: "tool_call",
      name: "get_job_logs",
      input: {},
    });
    expect(digging.extraTools).toEqual(["get_job_logs"]);

    const done = reduceExplanationEvent(digging, { type: "done", answer: "Solver too old." });
    expect(done.status).toBe("success");
    expect(done.answer).toBe("Solver too old.");
  });

  test("keeps the conversation of the explanation, to continue it with questions", () => {
    const history = [{ role: "user", content: "Why did the job fail?" }];
    const done = reduceExplanationEvent(RUNNING_EXPLANATION_STATE, {
      type: "done",
      answer: "Solver too old.",
      history,
    });

    expect(done.history).toEqual(history);
  });

  test("keeps the reason when the job could not be read", () => {
    const state = reduceExplanationEvent(RUNNING_EXPLANATION_STATE, {
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
    const stream = mockStream();
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

    stream.send({ type: "done", answer: "The solver **8.8** cannot read a 9.2 study." });
    stream.end();

    expect(screen.getByText("8.8")).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "tasks.explain.restart" })).toBeInTheDocument();
  });

  test("shows the advice of the rules when the assistant fails", async () => {
    const stream = mockStream();
    renderExplanation();
    await userEvent.click(await screen.findByRole("button", { name: "tasks.explain.button" }));

    stream.send(DIAGNOSE_RESULT);
    stream.send({ type: "error", message: "The Anthropic API rate limit is reached." });
    stream.end();

    expect(screen.getByText("The Anthropic API rate limit is reached.")).toBeInTheDocument();
    // Without the explanation of the assistant, the explanation of the rule is the fallback
    expect(screen.getByText(/Launch again with a more recent solver/)).toBeInTheDocument();
  });

  describe("questions about the cause", () => {
    test("continue the conversation of the explanation", async () => {
      const chat = mockChat();
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

      await userEvent.type(screen.getByRole("textbox", { name: ASK }), "And then?{Enter}");

      expect(chat.requests[1]).toMatchObject({ history: THREAD_HISTORY, message: "And then?" });
    });

    test("wait for the explanation", async () => {
      const stream = mockStream();
      renderExplanation();
      await userEvent.click(await screen.findByRole("button", { name: "tasks.explain.button" }));

      stream.send(DIAGNOSE_RESULT);

      expect(screen.queryByRole("textbox", { name: ASK })).not.toBeInTheDocument();
    });

    test("are not offered when the assistant could not explain", async () => {
      const stream = mockStream();
      renderExplanation();
      await userEvent.click(await screen.findByRole("button", { name: "tasks.explain.button" }));

      stream.send({ type: "error", message: "The Anthropic API rate limit is reached." });
      stream.end();

      expect(screen.queryByRole("textbox", { name: ASK })).not.toBeInTheDocument();
    });

    test("are kept when the dialog is closed and reopened", async () => {
      const chat = mockChat();
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
      const chat = mockChat();
      await explain();
      await userEvent.type(screen.getByRole("textbox", { name: ASK }), "Which solver?{Enter}");
      chat.send({ type: "done", answer: "Use the solver 10.2.", history: THREAD_HISTORY });
      await chat.end();

      await userEvent.click(screen.getByRole("button", { name: "tasks.explain.restart" }));

      expect(screen.queryByText("Use the solver 10.2.")).not.toBeInTheDocument();
    });
  });
});
