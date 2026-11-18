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
import { mockAssistantStream } from "@/tests/assistantStream";
import { createQueryClient, createQueryWrapper } from "@/tests/queryUtils";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import AssistantChat from "..";
import {
  describeToolCall,
  INITIAL_CHAT_STATE,
  reduceChatEvent,
  startTurn,
} from "@/components/AssistantConversation/utils";

vi.mock("@/services/api/assistant", () => ({
  getAssistantStatus: vi.fn(),
  streamAssistantChat: vi.fn(),
}));

const STATUS = { available: true, readOnly: false };

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

  test("reduceChatEvent tells whether each tool call is running or done", () => {
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

    expect(state.turns[0].tools[0].status).toBe("done");
  });
});

describe("AssistantChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getAssistantStatus).mockResolvedValue(STATUS);
  });

  test("sends a message, shows the actions of the assistant, then its answer", async () => {
    const stream = mockAssistantStream(streamAssistantChat);
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
    const stream = mockAssistantStream(streamAssistantChat);
    await openChat();

    await sendMessage("Hello");
    stream.send({ type: "error", message: "The model server rejected the API key." });
    await stream.end();

    expect(screen.getByText("The model server rejected the API key.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "study.assistant.send" })).toBeDisabled();
  });

  test("stops a running answer and starts a new conversation", async () => {
    const stream = mockAssistantStream(streamAssistantChat);
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
