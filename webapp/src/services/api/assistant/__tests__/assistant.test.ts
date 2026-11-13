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

import { vi } from "vitest";
import { createLineSplitter, streamStudyCheck } from "..";
import type { AssistantEvent } from "../types";

vi.mock("@/redux/store", () => ({
  default: { dispatch: () => ({ unwrap: () => Promise.resolve({ accessToken: "user-token" }) }) },
}));

vi.mock("@/redux/ducks/auth", () => ({ refresh: () => ({ type: "auth/REFRESH" }) }));

vi.mock("../../client", () => ({
  default: { defaults: { baseURL: "http://antares.test" }, get: vi.fn() },
}));

function streamOf(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();

  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
}

function check(onEvent: (event: AssistantEvent) => void) {
  return streamStudyCheck({
    studyId: "study-1",
    language: "fr",
    signal: new AbortController().signal,
    onEvent,
  });
}

describe("createLineSplitter", () => {
  test("gives complete lines only, whatever the chunks", () => {
    const splitter = createLineSplitter();

    expect(splitter.push('{"a": 1}\n{"b"')).toEqual(['{"a": 1}']);
    expect(splitter.push(": 2}\n\n")).toEqual(['{"b": 2}']);
    expect(splitter.push('{"c": 3}')).toEqual([]);
    expect(splitter.flush()).toEqual(['{"c": 3}']);
    expect(splitter.flush()).toEqual([]);
  });
});

describe("streamStudyCheck", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  test("reads the events as they arrive, with the token of the user", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        new Response(
          streamOf([
            '{"type": "tool_call", "name": "check_study", "input": {"deep": true}}\n{"type": "tool_pro',
            'gress", "name": "check_study", "progress": 1, "total": 5, "message": "Checking x_y"}\n',
            '{"type": "from_a_newer_server"}\nnot json\n',
            '{"type": "done", "answer": "Étude prête.", "history": []}',
          ]),
        ),
      );
    vi.stubGlobal("fetch", fetchMock);
    const events: AssistantEvent[] = [];

    await check((event) => events.push(event));

    expect(events.map((event) => event.type)).toEqual(["tool_call", "tool_progress", "done"]);
    expect(events[2]).toMatchObject({ answer: "Étude prête." });
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("http://antares.test/v1/assistant/studies/study-1/check?language=fr");
    expect(options).toMatchObject({
      method: "POST",
      headers: { Authorization: "Bearer user-token" },
    });
  });

  test("throws the reason given by the server", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify({ detail: "No API key for the assistant" }), { status: 503 }),
        ),
    );

    await expect(check(vi.fn())).rejects.toThrow("No API key for the assistant");
  });
});
