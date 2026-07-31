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

import { WsChannel, WsEventType } from "@/services/webSocket/constants";
import type { TaskEventPayload, WsEvent } from "@/services/webSocket/types";
import {
  addWsEventListener,
  removeWsEventListener,
  subscribeWsChannels,
  unsubscribeWsChannels,
} from "@/services/webSocket/ws";
import * as RA from "ramda-adjunct";
import { useEffect } from "react";
import { useLatest } from "react-use";

interface UseTaskMonitorOptions {
  taskIds?: string | string[];
  onCompleted: (payload: TaskEventPayload) => void;
  onFailed: (payload: TaskEventPayload) => void;
}

function getChannel(taskId: string) {
  return WsChannel.Task + taskId;
}

function useTasksMonitor({ taskIds, onCompleted, onFailed }: UseTaskMonitorOptions) {
  const callbacksRef = useLatest({ onCompleted, onFailed });

  useEffect(() => {
    if (!taskIds) {
      return;
    }

    const ids = RA.ensureArray(taskIds);
    const channels = ids.map(getChannel);

    subscribeWsChannels(channels);

    const listener = (event: WsEvent) => {
      switch (event.type) {
        case WsEventType.TaskCompleted:
        case WsEventType.TaskFailed: {
          const { id } = event.payload;

          if (ids.includes(id)) {
            unsubscribeWsChannels(getChannel(id));

            if (event.type === WsEventType.TaskCompleted) {
              callbacksRef.current.onCompleted(event.payload);
            } else {
              callbacksRef.current.onFailed(event.payload);
            }
          }

          break;
        }
      }
    };

    addWsEventListener(listener);

    return () => {
      removeWsEventListener(listener);
      unsubscribeWsChannels(channels);
    };
  }, [taskIds, callbacksRef]);
}

export default useTasksMonitor;
