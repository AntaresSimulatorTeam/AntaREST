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

import type { AssistantEvent, StreamHandlers } from "@/services/api/assistant/types";
import { toError } from "@/utils/fnUtils";
import { useEffect, useRef, useState } from "react";

export type RunStatus = "idle" | "running" | "success" | "error";

/**
 * Runs a request to the AI assistant which gives one result (the check of a study, the
 * explanation of a failure) and follows it, event after event.
 *
 * The state lives as long as the component: the result stays available after the panel showing
 * it is closed. A running request is stopped when the component unmounts.
 *
 * @param initialState - State before the first run, and after a cancelled one.
 * @param reduce - Computes the next state from an event of the assistant.
 * @param stream - Calls the endpoint with the given abort signal and event callback.
 * @returns The state, with `start` (which replaces a previous run), `cancel` (which stops a running
 * request) and `reset` (which also forgets the result).
 */
function useAssistantRun<S extends { status: RunStatus; error?: string }>(
  initialState: S,
  reduce: (state: S, event: AssistantEvent) => S,
  stream: (handlers: StreamHandlers) => Promise<void>,
) {
  const [state, setState] = useState(initialState);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => controllerRef.current?.abort();
  }, []);

  const cancel = () => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setState((prev) => (prev.status === "running" ? initialState : prev));
  };

  const reset = () => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setState(initialState);
  };

  const start = async () => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    // Events of a cancelled or replaced run are ignored
    const update = (next: (prev: S) => S) => {
      if (controllerRef.current === controller) {
        setState(next);
      }
    };
    setState({ ...initialState, status: "running" });

    try {
      await stream({
        signal: controller.signal,
        onEvent: (event) => update((prev) => reduce(prev, event)),
      });
      // The stream ended without a final event
      update((prev) => (prev.status === "running" ? { ...prev, status: "error" } : prev));
    } catch (err) {
      update((prev) => ({ ...prev, status: "error", error: toError(err).message }));
    }
  };

  return { state, start, cancel, reset };
}

export default useAssistantRun;
