/* eslint-disable no-use-before-define */
/* eslint-disable camelcase */
import debug from "debug";
import { Action } from "redux";
import { ThunkAction } from "redux-thunk";
import moment from "moment";
import { UserInfo, WSMessage } from "../common/types";
import { AppState } from "./reducers";
import { getConfig } from "../services/config";
import { refresh } from "../services/api/auth";
import { loginUser } from "./auth";

const logInfo = debug("antares:websocket:info");
const logError = debug("antares:websocket:error");

/** ******************************************* */
/* State                                        */
/** ******************************************* */

export interface WebsocketState {
  socket?: WebSocket;
  listeners: Array<(msg: WSMessage) => void>;
  connected: boolean;
  channels: Array<string>;
}

const initialState: WebsocketState = {
  listeners: [],
  connected: false,
  channels: [],
};

/** ******************************************* */
/* Actions                                      */
/** ******************************************* */

interface SubscribeAction extends Action {
  type: "WS/SUBSCRIBE";
  payload: string;
}

export const sendSubscribeMessage = (
  channels: string | Array<string>,
  websocket?: WebSocket
): void => {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    if (Array.isArray(channels)) {
      // TODO: Allow multi subscription
      channels.forEach((elm) => {
        if (websocket !== undefined) {
          websocket.send(
            JSON.stringify({
              action: "SUBSCRIBE",
              payload: elm,
            })
          );
        }
      });
    } else {
      websocket.send(
        JSON.stringify({
          action: "SUBSCRIBE",
          payload: channels,
        })
      );
    }
  }
};

export const subscribe =
  (channel: string): ThunkAction<void, AppState, unknown, WebsocketAction> =>
  (dispatch, getState): void => {
    const { websockets } = getState();
    sendSubscribeMessage(channel, websockets.socket);
    dispatch({
      type: "WS/SUBSCRIBE",
      payload: channel,
    });
  };

interface UnSubscribeAction extends Action {
  type: "WS/UNSUBSCRIBE";
  payload: string;
}

export const unsubscribe =
  (channel: string): ThunkAction<void, AppState, unknown, WebsocketAction> =>
  (dispatch, getState): void => {
    const { websockets } = getState();
    if (websockets.socket && websockets.socket.readyState === WebSocket.OPEN) {
      websockets.socket.send(
        JSON.stringify({
          action: "UNSUBSCRIBE",
          payload: channel,
        })
      );
    }
    dispatch({
      type: "WS/UNSUBSCRIBE",
      payload: channel,
    });
  };

export interface DisconnectAction extends Action {
  type: "WS/DISCONNECT";
}

export const disconnectWebsocket =
  (): ThunkAction<void, AppState, unknown, DisconnectAction> =>
  (dispatch, getState): void => {
    const { websockets } = getState();
    if (websockets.socket) {
      websockets.socket.close();
    }
    dispatch({
      type: "WS/DISCONNECT",
    });
  };

export interface NotifyConnectedAction extends Action {
  type: "WS/UPDATE_CONNECTION_STATUS";
  payload: boolean;
}

export const notifyConnected = (status: boolean): NotifyConnectedAction => ({
  type: "WS/UPDATE_CONNECTION_STATUS",
  payload: status,
});

export interface ConnectAction extends Action {
  type: "WS/CONNECT";
  payload: WebSocket;
}

const RECONNECTION_DEFAULT_DELAY = 3000;
// eslint-disable-next-line no-undef
let reconnectionTimer: NodeJS.Timeout | null = null;

export const connectWebsocket =
  (user?: UserInfo): ThunkAction<void, AppState, unknown, Action> =>
  (dispatch, getState): void => {
    const config = getConfig();
    const { websockets } = getState();

    const reconnectLoop = (): void => {
      if (!reconnectionTimer) {
        logInfo(`Reconnecting websocket in ${RECONNECTION_DEFAULT_DELAY}ms`);
        const current_user = getState().auth.user;
        reconnectionTimer = setTimeout(() => {
          dispatch(disconnectWebsocket());
          dispatch(connectWebsocket(current_user));
          reconnectionTimer = null;
        }, RECONNECTION_DEFAULT_DELAY);
      } else {
        logInfo("Already trying to reconnect to websockets");
      }
    };

    if (websockets.socket) {
      logInfo("Websocket exists, skipping reconnection");
      return;
    }

    try {
      if (user && user.expirationDate && user.expirationDate < moment()) {
        refresh(
          user,
          (updatedUser: UserInfo) => dispatch(loginUser(updatedUser)),
          () => {
            /* noop */
          }
        )
          .then((updatedUser?: UserInfo) => {
            if (!updatedUser) {
              reconnectionTimer = null;
              reconnectLoop();
            }
          })
          .catch((e) => {
            logError("Should not happen because refresh is already guarded", e);
            reconnectionTimer = null;
            reconnectLoop();
          });
        return;
      }

      const socket = new WebSocket(
        `${config.wsUrl + config.wsEndpoint}?token=${user?.accessToken}`
      );

      if (socket) {
        socket.onopen = (): void => {
          dispatch(notifyConnected(true));
          if (reconnectionTimer) {
            clearTimeout(reconnectionTimer);
            reconnectionTimer = null;
          }
          const { channels } = getState().websockets;
          sendSubscribeMessage(channels, websockets.socket);
        };
        socket.onclose = (): void => {
          logInfo("Websocket connexion is closed");
          dispatch(notifyConnected(false));
          reconnectLoop();
        };
        socket.onerror = (ev): void => {
          logError("Websocket error", ev);
        };
        socket.onmessage = (ev: MessageEvent): void => {
          const message: WSMessage = JSON.parse(ev.data);
          logInfo("Received websocket message", message);
          websockets.listeners.forEach((l) => {
            l(message);
          });
        };
        dispatch({
          type: "WS/CONNECT",
          payload: socket,
        });
      }
    } catch (e) {
      logError("Failed to connect to websockets", e);
      reconnectionTimer = null;
    }
  };

export const reconnectWebsocket =
  (user?: UserInfo): ThunkAction<void, AppState, unknown, Action> =>
  (dispatch): void => {
    dispatch(disconnectWebsocket());
    dispatch(connectWebsocket(user));
  };

export interface RefreshHandlersAction extends Action {
  type: "WS/REFRESH_HANDLERS";
}

const refreshHandlers = (state: WebsocketState): void => {
  if (state.socket) {
    // eslint-disable-next-line no-param-reassign
    state.socket.onmessage = (ev: MessageEvent): void => {
      const message: WSMessage = JSON.parse(ev.data);
      logInfo("Processing logs", message, state.listeners);
      state.listeners.forEach((l) => {
        l(message);
      });
    };
  }
};

interface AddListenerAction extends Action {
  type: "WS/ADD_LISTENER";
  payload: (ev: WSMessage) => void;
}

export const addListenerAction = (
  callback: (ev: WSMessage) => void
): AddListenerAction => ({
  type: "WS/ADD_LISTENER",
  payload: callback,
});

export const refreshHandlerAction = (): RefreshHandlersAction => ({
  type: "WS/REFRESH_HANDLERS",
});

export const addListener =
  (
    callback: (ev: WSMessage) => void
  ): ThunkAction<void, AppState, unknown, WebsocketAction> =>
  (dispatch): void => {
    dispatch({
      type: "WS/ADD_LISTENER",
      payload: callback,
    });
    dispatch({
      type: "WS/REFRESH_HANDLERS",
    });
  };

interface RemoveListenerAction extends Action {
  type: "WS/REMOVE_LISTENER";
  payload: (ev: WSMessage) => void;
}

export const removeListener =
  (
    callback: (ev: WSMessage) => void
  ): ThunkAction<void, AppState, unknown, WebsocketAction> =>
  (dispatch): void => {
    dispatch({
      type: "WS/REMOVE_LISTENER",
      payload: callback,
    });
    dispatch({
      type: "WS/REFRESH_HANDLERS",
    });
  };

export const WsChannel = {
  JOB_STATUS: "JOB_STATUS/",
  JOB_LOGS: "JOB_LOGS/",
  TASK: "TASK/",
  STUDY_GENERATION: "GENERATION_TASK/",
};

type WebsocketAction =
  | ConnectAction
  | DisconnectAction
  | AddListenerAction
  | RemoveListenerAction
  | RefreshHandlersAction
  | NotifyConnectedAction
  | SubscribeAction
  | UnSubscribeAction;

/** ******************************************* */
/* Selectors                                    */
/** ******************************************* */

/** ******************************************* */
/* Reducer                                      */
/** ******************************************* */

// eslint-disable-next-line default-param-last
export default (
  state = initialState,
  action: WebsocketAction
): WebsocketState => {
  switch (action.type) {
    case "WS/CONNECT":
      return {
        ...state,
        socket: action.payload,
      };
    case "WS/DISCONNECT": {
      const newState = {
        ...state,
      };
      delete newState.socket;
      return newState;
    }
    case "WS/UPDATE_CONNECTION_STATUS": {
      return {
        ...state,
        connected: action.payload,
      };
    }
    case "WS/REMOVE_LISTENER":
      return {
        ...state,
        listeners: state.listeners.filter((l) => l !== action.payload),
      };
    case "WS/ADD_LISTENER":
      return {
        ...state,
        listeners: state.listeners.concat(action.payload),
      };
    case "WS/REFRESH_HANDLERS":
      refreshHandlers(state);
      return {
        ...state,
      };
    case "WS/SUBSCRIBE":
      return {
        ...state,
        channels: state.channels.concat(action.payload),
      };
    case "WS/UNSUBSCRIBE":
      return {
        ...state,
        channels: state.channels.filter((l) => l !== action.payload),
      };
    default:
      return state;
  }
};
