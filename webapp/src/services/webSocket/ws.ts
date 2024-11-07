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
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import { LaunchJobDTO, UserInfo } from "../../common/types";
import { getConfig } from "../config";
import { isStringEmpty, isUserExpired } from "../utils";
import { AppDispatch } from "../../redux/store";
import { refresh as refreshUser } from "../../redux/ducks/auth";
import { deleteStudy, setStudy } from "../../redux/ducks/studies";
import {
  setMaintenanceMode,
  setMessageInfo,
  setWebSocketConnected,
} from "../../redux/ducks/ui";
import { refreshStudySynthesis } from "../../redux/ducks/studySyntheses";
import type { WsEvent, WsEventListener } from "./types";
import { WsChannel, WsEventType } from "./constants";

const logInfo = debug("antares:websocket:info");
const logError = debug("antares:websocket:error");

const RECONNECTION_DEFAULT_DELAY = 3000;

let webSocket: WebSocket | null;
let eventListeners: WsEventListener[] = [];
let channelSubscribed = new Set<string>();
let reconnectTimerId: NodeJS.Timeout | null = null;

let globalListenerAdded = false;

export function initWs(dispatch: AppDispatch, user?: UserInfo): WebSocket {
  if (webSocket) {
    logInfo("Websocket exists, skipping reconnection");
    return webSocket;
  }

  const config = getConfig();

  webSocket = new WebSocket(
    `${config.wsUrl + config.wsEndpoint}?token=${user?.accessToken}`,
  );

  if (!globalListenerAdded) {
    eventListeners.push(
      makeStudyListener(dispatch),
      makeStudyJobStatusListener(dispatch),
      makeMaintenanceListener(dispatch),
      makeStudyDataListener(dispatch),
    );
    globalListenerAdded = true;
  }

  webSocket.onmessage = (event: MessageEvent): void => {
    const message = JSON.parse(event.data) as WsEvent;
    logInfo("WebSocket message received", message);
    eventListeners.forEach((listener) => listener(message));
  };

  webSocket.onerror = (event): void => {
    logError("WebSocket error", event);
  };

  webSocket.onopen = (): void => {
    logInfo("WebSocket connection opened");
    dispatch(setWebSocketConnected(true));
    subscribeWsChannels([...channelSubscribed]);
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
          reloadWs(dispatch, user);
        }
      }, RECONNECTION_DEFAULT_DELAY);
    }

    reconnect();
  };

  return webSocket;
}

export function addWsEventListener(listener: WsEventListener) {
  eventListeners.push(listener);

  return () => {
    removeWsEventListener(listener);
  };
}

export function removeWsEventListener(listener: WsEventListener) {
  eventListeners = eventListeners.filter((l) => l !== listener);
}

function send(action: "SUBSCRIBE" | "UNSUBSCRIBE", payload: string) {
  webSocket?.send(JSON.stringify({ action, payload }));
}

export function subscribeWsChannels(channels: string | string[]) {
  const channelList = R.uniq(RA.ensureArray(channels));

  if (webSocket?.readyState === WebSocket.OPEN) {
    for (const channel of channelList) {
      if (!channelSubscribed.has(channel)) {
        send("SUBSCRIBE", channel);
      }
    }
  }

  channelList.forEach((channel) => {
    channelSubscribed.add(channel);
  });

  return () => {
    unsubscribeWsChannels(channelList);
  };
}

export function unsubscribeWsChannels(channels?: string | string[]) {
  const channelList = channels
    ? R.uniq(RA.ensureArray(channels))
    : [...channelSubscribed];

  if (webSocket?.readyState === WebSocket.OPEN) {
    for (const channel of channelList) {
      if (channelSubscribed.has(channel)) {
        send("UNSUBSCRIBE", channel);
      }
    }
  }

  channelList.forEach((channel) => {
    channelSubscribed.delete(channel);
  });
}

export function closeWs(clean = true) {
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
    eventListeners = [];
    channelSubscribed = new Set();
    globalListenerAdded = false;
  }
}

export function reloadWs(dispatch: AppDispatch, user?: UserInfo) {
  closeWs(false);
  return initWs(dispatch, user);
}

////////////////////////////////////////////////////////////////
// App Listeners
////////////////////////////////////////////////////////////////

function makeStudyListener(dispatch: AppDispatch): WsEventListener {
  return function listener(e: WsEvent) {
    switch (e.type) {
      case WsEventType.StudyCreated:
      case WsEventType.StudyEdited:
        dispatch(setStudy(e.payload));
        break;
      case WsEventType.StudyDeleted:
        dispatch(deleteStudy(e.payload));
        break;
    }
  };
}

function makeStudyJobStatusListener(dispatch: AppDispatch): WsEventListener {
  const unsubscribeById: Record<LaunchJobDTO["id"], VoidFunction> = {};

  return function listener(e: WsEvent) {
    switch (e.type) {
      case WsEventType.StudyJobStarted: {
        const unsubscribe = subscribeWsChannels(
          WsChannel.JobStatus + e.payload.id,
        );
        unsubscribeById[e.payload.id] = unsubscribe;
        break;
      }
      case WsEventType.StudyJobCompleted:
        unsubscribeById[e.payload.id]?.();
        dispatch(refreshStudySynthesis(e.payload));
        break;
    }
  };
}

function makeStudyDataListener(dispatch: AppDispatch): WsEventListener {
  return function listener(e: WsEvent) {
    switch (e.type) {
      case WsEventType.StudyDataEdited:
        dispatch(refreshStudySynthesis(e.payload));
        break;
    }
  };
}

function makeMaintenanceListener(dispatch: AppDispatch): WsEventListener {
  return function listener(e: WsEvent) {
    switch (e.type) {
      case WsEventType.MaintenanceMode:
        dispatch(setMaintenanceMode(e.payload));
        break;
      case WsEventType.MessageInfo:
        dispatch(
          setMessageInfo(isStringEmpty(e.payload) ? "" : (e.payload as string)),
        );
        break;
    }
  };
}
