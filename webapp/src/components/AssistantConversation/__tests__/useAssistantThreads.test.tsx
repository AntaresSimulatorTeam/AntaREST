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

import { streamAssistantChat } from "@/services/api/assistant";
import { mockAssistantStream } from "@/tests/assistantStream";
import { createQueryClient, createQueryWrapper } from "@/tests/queryUtils";
import { act, renderHook, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import useAssistantThreads from "../useAssistantThreads";

vi.mock("@/services/api/assistant", () => ({
  streamAssistantChat: vi.fn(),
}));

const BASE_HISTORY = [{ role: "user", content: "Check this study" }];
const THREAD_HISTORY = [...BASE_HISTORY, { role: "user", content: "Why?" }];
const CONTEXT = "[The user is looking at the finding X]";

function renderThreads() {
  const queryClient = createQueryClient();
  const invalidateQueries = vi.spyOn(queryClient, "invalidateQueries");
  const { result } = renderHook(() => useAssistantThreads("study-1"), {
    wrapper: createQueryWrapper(queryClient),
  });

  return {
    result,
    invalidateQueries,
    ask: (key: string, message: string) =>
      act(() => {
        result.current.send(key, { message, context: CONTEXT, baseHistory: BASE_HISTORY });
      }),
  };
}

describe("useAssistantThreads", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("starts a thread with its context, continuing the given conversation", async () => {
    const stream = mockAssistantStream(streamAssistantChat);
    const { result, ask } = renderThreads();

    ask("finding-0", "Why?");

    expect(stream.requests[0]).toMatchObject({
      studyId: "study-1",
      history: BASE_HISTORY,
      message: `${CONTEXT}\n\nWhy?`,
    });
    // The context is for the assistant: the user sees their own words
    expect(result.current.threads["finding-0"].turns[0].question).toBe("Why?");
    expect(result.current.threads["finding-0"].isRunning).toBe(true);

    stream.send({ type: "done", answer: "Because.", history: THREAD_HISTORY });
    await stream.end();

    expect(result.current.threads["finding-0"].turns[0].answer).toBe("Because.");
    expect(result.current.threads["finding-0"].isRunning).toBe(false);
  });

  test("continues a thread with its own history, without repeating the context", async () => {
    const stream = mockAssistantStream(streamAssistantChat);
    const { ask } = renderThreads();
    ask("finding-0", "Why?");
    stream.send({ type: "done", answer: "Because.", history: THREAD_HISTORY });
    await stream.end();

    ask("finding-0", "How to fix it?");

    expect(stream.requests[1]).toMatchObject({
      history: THREAD_HISTORY,
      message: "How to fix it?",
    });
  });

  test("sends the context again when the first message got no answer", async () => {
    const stream = mockAssistantStream(streamAssistantChat);
    const { result, ask } = renderThreads();
    ask("finding-0", "Why?");
    stream.send({ type: "error", message: "The rate limit of the model server is reached." });
    await stream.end();
    expect(result.current.threads["finding-0"].turns[0].error).toBe(
      "The rate limit of the model server is reached.",
    );

    ask("finding-0", "Why?");

    expect(stream.requests[1]).toMatchObject({
      history: BASE_HISTORY,
      message: `${CONTEXT}\n\nWhy?`,
    });
  });

  test("reports a stream which ends without an answer", async () => {
    const stream = mockAssistantStream(streamAssistantChat);
    const { result, ask } = renderThreads();
    ask("finding-0", "Why?");

    await stream.end();

    expect(result.current.threads["finding-0"].turns[0].error).toBe("study.assistant.noAnswer");
    expect(result.current.threads["finding-0"].isRunning).toBe(false);
  });

  test("reports a rejected request in the thread", async () => {
    vi.mocked(streamAssistantChat).mockRejectedValue(new Error("No API key for the assistant"));
    const { result, ask } = renderThreads();

    ask("finding-0", "Why?");

    await waitFor(() =>
      expect(result.current.threads["finding-0"].turns[0].error).toBe(
        "No API key for the assistant",
      ),
    );
  });

  test("keeps the threads apart", async () => {
    const stream = mockAssistantStream(streamAssistantChat);
    const { result, ask } = renderThreads();
    ask("finding-0", "Why?");
    ask("finding-1", "And this one?");

    // The answer of the first thread arrives while the second is still running
    stream.send({ type: "done", answer: "Because.", history: THREAD_HISTORY }, 0);
    await stream.end(0);

    expect(result.current.threads["finding-0"].turns[0].answer).toBe("Because.");
    expect(result.current.threads["finding-1"].turns[0].answer).toBe("");
    expect(result.current.threads["finding-1"].isRunning).toBe(true);
  });

  test("ignores a message sent while the thread is answering", () => {
    const stream = mockAssistantStream(streamAssistantChat);
    const { result, ask } = renderThreads();
    ask("finding-0", "Why?");

    ask("finding-0", "Hello?");

    expect(stream.requests).toHaveLength(1);
    expect(result.current.threads["finding-0"].turns).toHaveLength(1);
  });

  test("stops an answer", () => {
    const stream = mockAssistantStream(streamAssistantChat);
    const { result, ask } = renderThreads();
    ask("finding-0", "Why?");

    act(() => result.current.stop("finding-0"));

    expect(stream.requests[0].signal.aborted).toBe(true);
    expect(result.current.threads["finding-0"].isRunning).toBe(false);
    expect(result.current.threads["finding-0"].turns[0].error).toBe("study.assistant.stopped");

    // Events of the stopped answer are ignored
    stream.send({ type: "done", answer: "Too late." });
    expect(result.current.threads["finding-0"].turns[0].answer).toBe("");
  });

  test("reloads the data when the assistant may have changed the study", async () => {
    const stream = mockAssistantStream(streamAssistantChat);
    const { result, ask, invalidateQueries } = renderThreads();
    ask("finding-0", "Fix it");
    stream.send({ type: "tool_call", name: "update_thermal_cluster", input: {} });
    stream.send({
      type: "tool_result",
      name: "update_thermal_cluster",
      is_error: false,
      duration_s: 1,
    });
    stream.send({ type: "done", answer: "Fixed.", history: THREAD_HISTORY });

    await stream.end();

    expect(invalidateQueries).toHaveBeenCalled();
    expect(result.current.hasChangedData).toBe(true);
  });

  test("does not reload the data after an answer which only reads", async () => {
    const stream = mockAssistantStream(streamAssistantChat);
    const { result, ask, invalidateQueries } = renderThreads();
    ask("finding-0", "Why?");
    stream.send({ type: "tool_call", name: "list_areas", input: {} });
    stream.send({ type: "tool_call", name: "get_table", input: {} });
    stream.send({ type: "done", answer: "Because.", history: THREAD_HISTORY });

    await stream.end();

    expect(invalidateQueries).not.toHaveBeenCalled();
    expect(result.current.hasChangedData).toBe(false);
  });

  test("reset forgets the threads and stops the running answers", () => {
    const stream = mockAssistantStream(streamAssistantChat);
    const { result, ask } = renderThreads();
    ask("finding-0", "Why?");

    act(() => result.current.reset());

    expect(stream.requests[0].signal.aborted).toBe(true);
    expect(result.current.threads).toEqual({});
  });
});
