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
import type { AssistantEvent, AssistantHistory } from "@/services/api/assistant/types";
import { toError } from "@/utils/fnUtils";
import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  INITIAL_CHAT_STATE,
  lastTurnMayHaveChangedData,
  reduceChatEvent,
  startTurn,
  type ChatState,
} from "./utils";

export interface ThreadMessage {
  /** Message of the user, as shown in the thread. */
  message: string;
  /**
   * What the thread is about (e.g. a finding of a check), for the assistant. Sent before the
   * message of the user until the assistant has answered once; it is not shown in the thread.
   */
  context?: string;
  /** Conversation the thread continues (e.g. the one of the check), until it has its own. */
  baseHistory?: AssistantHistory;
}

function abortAll(controllers: Map<string, AbortController>) {
  for (const controller of controllers.values()) {
    controller.abort();
  }
}

/**
 * Conversations with the AI assistant about several subjects at once (e.g. one per finding of a
 * study check), each identified by a key.
 *
 * The threads live as long as the component: put the hook above what the user can close (drawer,
 * dialog), so that an answer goes on and the threads are kept when it is closed.
 *
 * @param studyId - Study the user is working on, if any.
 * @returns The threads by key, with `send`, `stop` and `reset`. `hasChangedData` tells whether the
 * assistant may have modified data in one of the threads.
 */
function useAssistantThreads(studyId?: string) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [threads, setThreads] = useState<Record<string, ChatState>>({});
  const [hasChangedData, setHasChangedData] = useState(false);
  // Latest threads, for the callbacks of the streams: they run between the renders
  const threadsRef = useRef(threads);
  const controllersRef = useRef(new Map<string, AbortController>());

  const setThread = useCallback((key: string, state: ChatState) => {
    threadsRef.current = { ...threadsRef.current, [key]: state };
    setThreads(threadsRef.current);
  }, []);

  const send = useCallback(
    async (key: string, { message, context, baseHistory = [] }: ThreadMessage) => {
      const thread = threadsRef.current[key] ?? INITIAL_CHAT_STATE;

      if (!message.trim() || thread.isRunning) {
        return;
      }

      const controller = new AbortController();
      controllersRef.current.set(key, controller);
      const isCurrent = () => controllersRef.current.get(key) === controller;
      // Events of a stopped or replaced answer are ignored
      const apply = (event: AssistantEvent) => {
        if (isCurrent()) {
          setThread(key, reduceChatEvent(threadsRef.current[key], event));
        }
      };
      // Without an answer yet, the assistant knows nothing about the subject of the thread
      const hasOwnHistory = thread.history.length > 0;
      setThread(key, startTurn(thread, message));

      try {
        await streamAssistantChat({
          message: !hasOwnHistory && context ? `${context}\n\n${message}` : message,
          studyId,
          history: hasOwnHistory ? thread.history : baseHistory,
          signal: controller.signal,
          onEvent: apply,
        });

        if (isCurrent() && threadsRef.current[key].isRunning) {
          // The stream ended without a final event
          apply({ type: "error", message: t("study.assistant.noAnswer") });
        }
      } catch (err) {
        apply({ type: "error", message: toError(err).message });
      }

      if (isCurrent() && lastTurnMayHaveChangedData(threadsRef.current[key])) {
        // The assistant may have modified the study: reload what is displayed
        setHasChangedData(true);
        queryClient.invalidateQueries();
      }
    },
    [studyId, queryClient, setThread, t],
  );

  const stop = useCallback(
    (key: string) => {
      controllersRef.current.get(key)?.abort();
      controllersRef.current.delete(key);
      const thread = threadsRef.current[key];

      if (thread?.isRunning) {
        setThread(
          key,
          reduceChatEvent(thread, { type: "error", message: t("study.assistant.stopped") }),
        );
      }
    },
    [setThread, t],
  );

  const reset = useCallback(() => {
    abortAll(controllersRef.current);
    controllersRef.current.clear();
    threadsRef.current = {};
    setThreads({});
    setHasChangedData(false);
  }, []);

  useEffect(() => {
    const controllers = controllersRef.current;
    return () => abortAll(controllers);
  }, []);

  return { threads, hasChangedData, send, stop, reset };
}

export default useAssistantThreads;
