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

import type { AssistantEvent } from "@/services/api/assistant/types";
import { act } from "@testing-library/react";
import { vi } from "vitest";
import { deferred } from "./queryUtils";

interface StreamParams {
  signal: AbortSignal;
  onEvent: (event: AssistantEvent) => void;
}

/**
 * Replaces a stream of the assistant API (a function mocked with `vi.mock`): each call gets its
 * own controllable stream.
 *
 * @param streamFn - The mocked function: `streamAssistantChat`, `streamStudyCheck`...
 * @returns The received requests, and functions to send an event to a request and to end it
 * (the last request by default).
 */
export function mockAssistantStream<P extends StreamParams>(
  streamFn: (params: P) => Promise<void>,
) {
  const requests: P[] = [];
  const ends: Array<ReturnType<typeof deferred<void>>> = [];

  vi.mocked(streamFn).mockImplementation((params) => {
    requests.push(params);
    const end = deferred<void>();
    ends.push(end);
    return end.promise;
  });

  return {
    requests,
    send: (event: AssistantEvent, index = requests.length - 1) =>
      act(() => requests[index].onEvent(event)),
    end: (index = ends.length - 1) =>
      act(async () => {
        ends[index].resolve();
        await ends[index].promise;
      }),
  };
}
