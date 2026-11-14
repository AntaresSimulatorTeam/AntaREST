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

import { getAssistantStatus, streamAssistantChat } from "@/services/api/assistant";
import type { AssistantEvent, StreamAssistantChatParams } from "@/services/api/assistant/types";
import { createQueryClient, createQueryWrapper, deferred } from "@/tests/queryUtils";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import AssistantChat from "..";
import {
  describeToolCall,
  INITIAL_CHAT_STATE,
  lastTurnMayHaveChangedData,
  reduceChatEvent,
  startTurn,
} from "../utils";

vi.mock("@/services/api/assistant", () => ({
  getAssistantStatus: vi.fn(),
  streamAssistantChat: vi.fn(),
}));

const STATUS = { available: true, reason: "", provider: "anthropic", model: "", readOnly: false };

/**
 * Replaces the stream of the server: each message sent gets its own controllable stream.
 *
 * @returns Functions to send an event and to end the current stream, and the received requests.
 */
function mockStream() {
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
    end: () => act(() => end.resolve()),
  };
}

async function openChat() {
  const queryClient = createQueryClient();
  render(<AssistantChat studyId="study-1" />, { wrapper: createQueryWrapper(queryClient) });
  await userEvent.click(await screen.findByRole("button", { name: "study.assistant.tooltip" }));
  return queryClient;
}

async function sendMessage(text: string) {
  await userEvent.type(screen.getByRole("textbox"), `${text}{Enter}`);
}

describe("chat utils", () => {
  test("describeToolCall leaves the study id out and shortens long arguments", () => {
    expect(describeToolCall("create_area", { study_id: "s1", name: "fr" })).toBe(
      "create_area(name=fr)",
    );
    expect(describeToolCall("list_areas", { study_id: "s1" })).toBe("list_areas()");
    expect(describeToolCall("get_table", { columns: ["a".repeat(60)] })).toMatch(/…\)$/);
  });

  test("reduceChatEvent follows a turn and keeps the history for the next one", () => {
    let state = startTurn(INITIAL_CHAT_STATE, "Create an area");
    state = reduceChatEvent(state, {
      type: "tool_call",
      name: "create_area",
      input: { name: "es" },
    });
    expect(state.turns[0].tools).toEqual([
      { name: "create_area", label: "create_area(name=es)", status: "running" },
    ]);

    state = reduceChatEvent(state, {
      type: "tool_result",
      name: "create_area",
      is_error: false,
      duration_s: 0.1,
    });
    state = reduceChatEvent(state, { type: "done", answer: "Done.", history: [{ role: "user" }] });

    expect(state.turns[0].tools[0].status).toBe("done");
    expect(state.turns[0].answer).toBe("Done.");
    expect(state.history).toEqual([{ role: "user" }]);
    expect(state.isRunning).toBe(false);
    expect(lastTurnMayHaveChangedData(state)).toBe(true);
  });

  test("a turn which only reads does not need a reload of the data", () => {
    let state = startTurn(INITIAL_CHAT_STATE, "Which areas?");
    state = reduceChatEvent(state, { type: "tool_call", name: "list_areas", input: {} });
    state = reduceChatEvent(state, { type: "tool_call", name: "get_table", input: {} });

    expect(lastTurnMayHaveChangedData(state)).toBe(false);
  });
});

describe("AssistantChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getAssistantStatus).mockResolvedValue(STATUS);
  });

  test("sends a message, shows the actions of the assistant, then its answer", async () => {
    const stream = mockStream();
    const queryClient = await openChat();
    const invalidate = vi.spyOn(queryClient, "invalidateQueries");
    expect(screen.getByText("study.assistant.readWrite")).toBeInTheDocument();

    await sendMessage("Create an area Spain");

    expect(stream.requests[0]).toMatchObject({
      message: "Create an area Spain",
      studyId: "study-1",
      history: [],
    });
    expect(screen.getByText("Create an area Spain")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toHaveValue("");
    expect(screen.getByText("study.assistant.working")).toBeInTheDocument();

    stream.send({
      type: "tool_call",
      name: "create_area",
      input: { study_id: "s", name: "Spain" },
    });
    expect(screen.getByText("create_area(name=Spain)")).toBeInTheDocument();

    stream.send({ type: "tool_result", name: "create_area", is_error: false, duration_s: 0.1 });
    stream.send({ type: "done", answer: "The area **Spain** is created.", history: [{ turn: 1 }] });
    await stream.end();

    expect(screen.getByText("Spain")).toBeInTheDocument();
    // The assistant modified the study: the displayed data is reloaded
    expect(invalidate).toHaveBeenCalled();

    // The next message continues the same conversation
    await sendMessage("And a link to France");

    expect(stream.requests[1]).toMatchObject({ history: [{ turn: 1 }] });
  });

  test("shows an error of the assistant in the conversation", async () => {
    const stream = mockStream();
    await openChat();

    await sendMessage("Hello");
    stream.send({ type: "error", message: "The Anthropic API key is invalid or revoked." });
    await stream.end();

    expect(screen.getByText("The Anthropic API key is invalid or revoked.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "study.assistant.send" })).toBeDisabled();
  });

  test("stops a running answer and starts a new conversation", async () => {
    const stream = mockStream();
    await openChat();
    await sendMessage("Hello");

    await userEvent.click(screen.getByRole("button", { name: "study.assistant.stop" }));

    expect(stream.requests[0].signal.aborted).toBe(true);
    expect(screen.getByText("study.assistant.stopped")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "study.assistant.newConversation" }));

    expect(screen.queryByText("Hello")).not.toBeInTheDocument();
    expect(screen.getByText("study.assistant.hint")).toBeInTheDocument();
  });
});
