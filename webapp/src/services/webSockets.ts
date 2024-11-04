/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import debug from "debug";
import * as RA from "ramda-adjunct";
import {
  GenericInfo,
  LaunchJobDTO,
  StudySummary,
  UserInfo,
  WSEvent,
  WSMessage,
} from "@/common/types";
import { getConfig } from "./config";
import { isStringEmpty, isUserExpired } from "./utils";
import { AppDispatch } from "@/redux/store";
import { refresh as refreshUser } from "@/redux/ducks/auth";
import { deleteStudy, setStudy } from "@/redux/ducks/studies";
import {
  setMaintenanceMode,
  setMessageInfo,
  setWebSocketConnected,
} from "@/redux/ducks/ui";
import { refreshStudySynthesis } from "@/redux/ducks/studySyntheses";

const logInfo = debug("antares:websocket:info");
const logError = debug("antares:websocket:error");

const RECONNECTION_DEFAULT_DELAY = 3000;

type MessageListener = (message: WSMessage) => void;

let webSocket: WebSocket | null;
let messageListeners = [] as MessageListener[];
let channelSubscriptions = [] as string[];
let reconnectTimerId: NodeJS.Timeout | null = null;

export enum WsChannel {
  JobStatus = "JOB_STATUS/",
  JobLogs = "JOB_LOGS/",
  Task = "TASK/",
  StudyGeneration = "GENERATION_TASK/",
}

let globalListenerAdded = false;

export function initWebSocket(
  dispatch: AppDispatch,
  user?: UserInfo,
): WebSocket {
  if (webSocket) {
    logInfo("Websocket exists, skipping reconnection");
    return webSocket;
  }

  const config = getConfig();

  webSocket = new WebSocket(
    `${config.wsUrl + config.wsEndpoint}?token=${user?.accessToken}`,
  );

  if (!globalListenerAdded) {
    messageListeners.push(
      makeStudyListener(dispatch),
      makeStudyJobStatusListener(dispatch),
      makeMaintenanceListener(dispatch),
      makeStudyDataListener(dispatch),
    );
    globalListenerAdded = true;
  }

  webSocket.onmessage = (event: MessageEvent): void => {
    const message = JSON.parse(event.data) as WSMessage;
    logInfo("WebSocket message received", message);
    messageListeners.forEach((listener) => listener(message));
  };

  webSocket.onerror = (event): void => {
    logError("WebSocket error", event);
  };

  webSocket.onopen = (): void => {
    logInfo("WebSocket connection opened");
    dispatch(setWebSocketConnected(true));
    sendWsSubscribeMessage(channelSubscriptions);
  };

  webSocket.onclose = (): void => {
    logInfo("WebSocket connection closed");
    dispatch(setWebSocketConnected(false));

    function reconnect(): void {
      logInfo("Attempt to reconnect to the WebSocket...");

      reconnectTimerId = setTimeout(() => {
        reconnectTimerId = null;
        if (user && isUserExpired(user)) {
          dispatch(refreshUser()) // Reload WebSocket is called inside
            .unwrap()
            .catch((err) => {
              logError(
                "Should not happen because refresh is already guarded",
                err,
              );
              reconnect();
            });
        } else {
          reloadWebSocket(dispatch, user);
        }
      }, RECONNECTION_DEFAULT_DELAY);
    }

    reconnect();
  };

  return webSocket;
}

export function addWsMessageListener(listener: MessageListener): VoidFunction {
  messageListeners.push(listener);
  // Remove listener callback
  return () => {
    messageListeners = messageListeners.filter((l) => l !== listener);
  };
}

export function sendWsSubscribeMessage(
  channels: string | string[],
): VoidFunction {
  const channelsList = RA.ensureArray(channels);

  function send(action: string): void {
    channelSubscriptions = channelSubscriptions.filter(
      (chan) => channelsList.indexOf(chan) === -1,
    );
    if (action === "SUBSCRIBE") {
      channelSubscriptions.push(...channelsList);
    }

    if (webSocket && webSocket.readyState === WebSocket.OPEN) {
      const socket: WebSocket = webSocket;
      const messagesToSend = channelsList.map((chan) =>
        JSON.stringify({ action, payload: chan }),
      );
      messagesToSend.forEach((msg) => socket.send(msg));
    }
  }

  send("SUBSCRIBE");

  // Unsubscribe callback
  return () => {
    send("UNSUBSCRIBE");
  };
}

export function closeWebSocket(clean = true): void {
  if (!webSocket) {
    return;
  }

  if (reconnectTimerId) {
    clearTimeout(reconnectTimerId);
    reconnectTimerId = null;
  }

  webSocket.onclose = (): void => {
    logInfo("WebSocket connection closed");
  };

  webSocket.close();

  webSocket = null;

  if (clean) {
    messageListeners = [];
    channelSubscriptions = [];
    globalListenerAdded = false;
  }
}

export function reloadWebSocket(
  dispatch: AppDispatch,
  user?: UserInfo,
): WebSocket {
  closeWebSocket(false);
  return initWebSocket(dispatch, user);
}

////////////////////////////////////////////////////////////////
// App Listeners
////////////////////////////////////////////////////////////////

function makeStudyListener(dispatch: AppDispatch) {
  return function listener(e: WSMessage<StudySummary>): void {
    switch (e.type) {
      case WSEvent.STUDY_CREATED:
      case WSEvent.STUDY_EDITED:
        dispatch(setStudy(e));
        break;
      case WSEvent.STUDY_DELETED:
        dispatch(deleteStudy(e));
        break;
    }
  };
}

function makeStudyJobStatusListener(dispatch: AppDispatch): MessageListener {
  const unsubscribeById: Record<LaunchJobDTO["id"], VoidFunction> = {};

  return function listener(e: WSMessage<LaunchJobDTO>): void {
    switch (e.type) {
      case WSEvent.STUDY_JOB_STARTED: {
        const unsubscribe = sendWsSubscribeMessage(
          WsChannel.JobStatus + e.payload.id,
        );
        unsubscribeById[e.payload.id] = unsubscribe;
        break;
      }
      case WSEvent.STUDY_JOB_COMPLETED:
        unsubscribeById[e.payload.id]?.();
        dispatch(refreshStudySynthesis(e));
        break;
    }
  };
}

function makeStudyDataListener(dispatch: AppDispatch) {
  return function listener(e: WSMessage<GenericInfo>): void {
    switch (e.type) {
      case WSEvent.STUDY_DATA_EDITED:
        dispatch(refreshStudySynthesis(e));
        break;
    }
  };
}

function makeMaintenanceListener(dispatch: AppDispatch) {
  return function listener(e: WSMessage): void {
    switch (e.type) {
      case WSEvent.MAINTENANCE_MODE:
        dispatch(setMaintenanceMode(e.payload as boolean));
        break;
      case WSEvent.MESSAGE_INFO:
        dispatch(
          setMessageInfo(
            isStringEmpty(e.payload as string) ? "" : (e.payload as string),
          ),
        );
        break;
    }
  };
}
