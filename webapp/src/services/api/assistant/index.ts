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
import { assistantEventSchema } from "./schemas";
import type { AssistantStatus, AssistantStatusDTO, StreamStudyCheckParams } from "./types";

const BASE_URL = "/v1/assistant";

export async function getAssistantStatus(): Promise<AssistantStatus> {
  const { data } = await client.get<AssistantStatusDTO>(BASE_URL);

  return {
    available: data.available,
    reason: data.reason,
    provider: data.provider,
    model: data.model,
    readOnly: data.read_only,
  };
}

/**
 * Splits a stream of text chunks into lines: a chunk can end in the middle of a line.
 *
 * @returns `push` gives the complete lines of a new chunk, `flush` gives the last line, if any.
 */
export function createLineSplitter() {
  let buffer = "";

  return {
    push(chunk: string): string[] {
      const lines = (buffer + chunk).split("\n");
      buffer = lines.pop() ?? "";
      return lines.filter((line) => line.trim() !== "");
    },
    flush(): string[] {
      const rest = buffer;
      buffer = "";
      return rest.trim() === "" ? [] : [rest];
    },
  };
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

/**
 * Checks a study with the AI assistant, calling `onEvent` for each event of the assistant as it
 * happens: progress of the rules, findings, then the report (or an error).
 *
 * Axios cannot read a response while it is being received in a browser, hence `fetch`.
 *
 * @param params - Study, language of the analysis, abort signal and event callback.
 * @throws If the request fails (the server explains why), or if it is aborted with `signal`.
 */
export async function streamStudyCheck(params: StreamStudyCheckParams): Promise<void> {
  const { studyId, language, signal, onEvent } = params;
  // Same as the axios client: refresh the access token if it is expired
  const user = await store.dispatch(refresh()).unwrap();
  const url = `${client.defaults.baseURL ?? ""}${BASE_URL}/studies/${encodeURIComponent(studyId)}/check?language=${language}`;

  const response = await fetch(url, {
    method: "POST",
    headers: user ? { Authorization: `Bearer ${user.accessToken}` } : undefined,
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(await getErrorMessage(response));
  }

  const handleLine = (line: string) => {
    let json: unknown;
    try {
      json = JSON.parse(line);
    } catch {
      return; // Not an event
    }
    const event = assistantEventSchema.safeParse(json);
    // Events added by a newer server are ignored
    if (event.success) {
      onEvent(event.data);
    }
  };

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  const splitter = createLineSplitter();

  for (;;) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    splitter.push(decoder.decode(value, { stream: true })).forEach(handleLine);
  }

  splitter.flush().forEach(handleLine);
}
