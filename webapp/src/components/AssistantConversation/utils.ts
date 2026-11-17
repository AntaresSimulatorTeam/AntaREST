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

import type { AssistantEvent, AssistantHistory } from "@/services/api/assistant/types";

const MAX_ARGUMENT_LENGTH = 40;

/** A tool call made by the assistant to answer a message. */
export interface ToolActivity {
  name: string;
  /** Short description of the call, e.g. `create_area(name=fr)`. */
  label: string;
  status: "running" | "done" | "error";
}

/** A message of the user, with what the assistant did and answered. */
export interface ChatTurn {
  id: number;
  question: string;
  tools: ToolActivity[];
  /** Answer of the assistant (Markdown); empty while it works. */
  answer: string;
  error?: string;
}

export interface ChatState {
  turns: ChatTurn[];
  /** State of the conversation for the server: sent back with the next message. */
  history: AssistantHistory;
  isRunning: boolean;
}

export const INITIAL_CHAT_STATE: ChatState = { turns: [], history: [], isRunning: false };

/**
 * Describes a tool call in one line.
 *
 * @param name - Name of the tool.
 * @param input - Arguments of the call.
 * @returns For instance `create_area(name=fr)`. The study id is left out: it is always the same.
 */
export function describeToolCall(name: string, input: Record<string, unknown>): string {
  const args = Object.entries(input)
    .filter(([key]) => key !== "study_id")
    .map(([key, value]) => {
      const text = typeof value === "string" ? value : JSON.stringify(value);
      const short =
        text.length > MAX_ARGUMENT_LENGTH ? `${text.slice(0, MAX_ARGUMENT_LENGTH - 1)}…` : text;
      return `${key}=${short}`;
    });

  return `${name}(${args.join(", ")})`;
}

/**
 * Adds a message of the user to a conversation.
 *
 * @param state - Current state of the conversation.
 * @param question - Message of the user.
 * @returns The new state, waiting for the assistant.
 */
export function startTurn(state: ChatState, question: string): ChatState {
  const turn: ChatTurn = { id: state.turns.length, question, tools: [], answer: "" };
  return { ...state, turns: [...state.turns, turn], isRunning: true };
}

function updateLastTurn(state: ChatState, update: (turn: ChatTurn) => ChatTurn): ChatState {
  const last = state.turns.at(-1);
  return last ? { ...state, turns: [...state.turns.slice(0, -1), update(last)] } : state;
}

/**
 * Computes the next state of a conversation from an event of the assistant.
 *
 * @param state - Current state of the conversation.
 * @param event - Event received from the assistant.
 * @returns The new state.
 */
export function reduceChatEvent(state: ChatState, event: AssistantEvent): ChatState {
  switch (event.type) {
    case "tool_call":
      return updateLastTurn(state, (turn) => ({
        ...turn,
        tools: [
          ...turn.tools,
          {
            name: event.name,
            label: describeToolCall(event.name, event.input),
            status: "running",
          },
        ],
      }));

    case "tool_result":
      return updateLastTurn(state, (turn) => {
        // Tools run one at a time: the result is the one of the last running call
        const index = turn.tools
          .map((tool) => tool.name === event.name && tool.status === "running")
          .lastIndexOf(true);
        return {
          ...turn,
          tools: turn.tools.map((tool, i) =>
            i === index ? { ...tool, status: event.is_error ? "error" : "done" } : tool,
          ),
        };
      });

    case "done":
      return {
        ...updateLastTurn(state, (turn) => ({ ...turn, answer: event.answer })),
        history: event.history ?? state.history,
        isRunning: false,
      };

    case "error":
      return {
        ...updateLastTurn(state, (turn) => ({ ...turn, error: event.message })),
        isRunning: false,
      };

    default:
      return state;
  }
}

/**
 * Tells whether the assistant may have changed data during the last turn.
 *
 * @param state - State of the conversation.
 * @returns True if the last turn called a tool which is not a read (`get_*`, `list_*`...).
 */
export function lastTurnMayHaveChangedData(state: ChatState): boolean {
  const readPrefixes = ["get_", "list_", "describe_", "summarize_", "check_", "read_", "diagnose_"];
  const tools = state.turns.at(-1)?.tools ?? [];
  return tools.some((tool) => !readPrefixes.some((prefix) => tool.name.startsWith(prefix)));
}
