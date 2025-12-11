/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import { useEffect } from "react";
import { WsChannel, WsEventType } from "@/services/webSocket/constants";
import type { WsEvent } from "@/services/webSocket/types";
import {
  addWsEventListener,
  removeWsEventListener,
  subscribeWsChannels,
  unsubscribeWsChannels,
} from "@/services/webSocket/ws";

interface UseTaskMonitorOptions {
  taskId: string | null;
  onComplete: () => void;
  onFailed: (message: string) => void;
}

export function useTaskMonitor({ taskId, onComplete, onFailed }: UseTaskMonitorOptions) {
  useEffect(() => {
    if (!taskId) {
      return;
    }

    const channel = WsChannel.Task + taskId;
    subscribeWsChannels([channel]);

    const handleTaskEvent = (event: WsEvent) => {
      if (event.type === WsEventType.TaskCompleted && event.payload.id === taskId) {
        onComplete();
        unsubscribeWsChannels([channel]);
      } else if (event.type === WsEventType.TaskFailed && event.payload.id === taskId) {
        onFailed(event.payload.message);
        unsubscribeWsChannels([channel]);
      }
    };

    addWsEventListener(handleTaskEvent);

    return () => {
      removeWsEventListener(handleTaskEvent);
      unsubscribeWsChannels([channel]);
    };
  }, [taskId, onComplete, onFailed]);
}
