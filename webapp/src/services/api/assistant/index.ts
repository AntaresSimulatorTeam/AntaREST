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

import { refresh } from "@/redux/ducks/auth";
import store from "@/redux/store";
import client from "../client";
import { assistantEventSchema, parseJson } from "./schemas";
import type {
  AssistantStatus,
  AssistantStatusDTO,
  StreamAssistantChatParams,
  StreamHandlers,
  StreamJobExplanationParams,
  StreamStudyCheckParams,
} from "./types";

const BASE_URL = "/v1/assistant";

export async function getAssistantStatus(): Promise<AssistantStatus> {
  const { data } = await client.get<AssistantStatusDTO>(BASE_URL);

  return { available: data.available, readOnly: data.read_only };
}

async function getErrorMessage(response: Response): Promise<string> {
  const text = await response.text();

  try {
    const body = JSON.parse(text) as { detail?: unknown; description?: unknown };
    const message = body.detail ?? body.description;
    return typeof message === "string" ? message : text;
  } catch {
    return text || `HTTP ${response.status}`;
  }
}

interface StreamParams extends StreamHandlers {
  /** Path of the endpoint, after `/v1/assistant`. */
  path: string;
  /** JSON body of the request, if any. */
  body?: unknown;
}

/**
 * Calls a streaming endpoint of the assistant, calling `onEvent` for each event as it happens.
 *
 * Axios cannot read a response while it is being received in a browser, hence `fetch`.
 *
 * @param params - Endpoint, body, abort signal and event callback.
 * @throws If the request fails (the server explains why), or if it is aborted with `signal`.
 */
async function streamAssistant(params: StreamParams): Promise<void> {
  const { path, body, signal, onEvent } = params;
  // Same as the axios client: refresh the access token if it is expired
  const user = await store.dispatch(refresh()).unwrap();

  const response = await fetch(`${client.defaults.baseURL ?? ""}${BASE_URL}${path}`, {
    method: "POST",
    headers: {
      ...(user && { Authorization: `Bearer ${user.accessToken}` }),
      ...(body !== undefined && { "Content-Type": "application/json" }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(await getErrorMessage(response));
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    // A chunk can end in the middle of a line: the rest waits for the next chunk
    const lines = (buffer + decoder.decode(value, { stream: !done })).split("\n");
    buffer = done ? "" : (lines.pop() ?? "");

    for (const line of lines) {
      // Blank lines, and events added by a newer server, are ignored
      const event = parseJson(assistantEventSchema, line);
      if (event) {
        onEvent(event);
      }
    }

    if (done) {
      break;
    }
  }
}

/**
 * Checks a study with the AI assistant: progress of the rules, findings, then the analysis.
 *
 * @param params - Study, language of the analysis, abort signal and event callback.
 * @returns A promise resolved when the assistant has finished.
 * @throws If the request fails or is aborted.
 */
export function streamStudyCheck(params: StreamStudyCheckParams): Promise<void> {
  const { studyId, language, signal, onEvent } = params;

  return streamAssistant({
    path: `/studies/${encodeURIComponent(studyId)}/check?language=${language}`,
    signal,
    onEvent,
  });
}

/**
 * Asks the AI assistant why a simulation failed: probable causes, then the explanation.
 *
 * @param params - Job, language of the explanation, abort signal and event callback.
 * @returns A promise resolved when the assistant has finished.
 * @throws If the request fails or is aborted.
 */
export function streamJobExplanation(params: StreamJobExplanationParams): Promise<void> {
  const { jobId, language, signal, onEvent } = params;

  return streamAssistant({
    path: `/jobs/${encodeURIComponent(jobId)}/explain?language=${language}`,
    signal,
    onEvent,
  });
}

/**
 * Sends a message to the AI assistant, in a conversation.
 *
 * @param params - Message, study the user works on, `history` of the previous answer, abort
 * signal and event callback.
 * @returns A promise resolved when the assistant has finished.
 * @throws If the request fails or is aborted.
 */
export function streamAssistantChat(params: StreamAssistantChatParams): Promise<void> {
  const { message, studyId, history, signal, onEvent } = params;

  return streamAssistant({
    path: "/chat/stream",

    body: { message, study_id: studyId, history },
    signal,
    onEvent,
  });
}
