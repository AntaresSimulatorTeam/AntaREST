/* eslint-disable camelcase */
/* eslint-disable @typescript-eslint/camelcase */
import { Action } from 'redux';
import { ThunkAction } from 'redux-thunk';
import { UserInfo } from '../common/types';
import { AppState } from '../App/reducers';
import { getConfig } from '../services/config';


/** ******************************************* */
/* State                                        */
/** ******************************************* */

export interface WebsocketState {
  socket?: WebSocket;
  listeners: Array<(ev: any) => void>;
}

const initialState: WebsocketState = {
  listeners: [],
};


/** ******************************************* */
/* Actions                                      */
/** ******************************************* */

export interface ConnectAction extends Action {
  type: 'WS/CONNECT';
  payload: WebSocket;
}

export const connectWebsocket = (user?: UserInfo): ThunkAction<void, AppState, unknown, ConnectAction> => (dispatch, getState): void => {
  const config = getConfig();
  const socket = new WebSocket(`${config.wsUrl + config.wsEndpoint}?token=${user?.accessToken }`);
  const { websockets } = getState();
  if (socket) {
    socket.onopen = (ev) => console.log(ev);
    socket.onclose = (ev) => console.log(ev)
    socket.onerror = (ev) => console.log(ev)   
    socket.onmessage = (message: any) => {
      websockets.listeners.forEach((l) => {
        l(message);
      });
    }
    dispatch({
      type: 'WS/CONNECT',
      payload: socket,
    });  
  }
};

export interface DisconnectAction extends Action {
  type: 'WS/DISCONNECT';
}

export const disconnectWebsocket = (): ThunkAction<void, AppState, unknown, DisconnectAction> => (dispatch, getState): void => {
  const { websockets } = getState();
  if (websockets.socket) {
    websockets.socket.close();
  }
  dispatch({
    type: 'WS/DISCONNECT',
  });
};

export const reconnectWebsocket = (user?: UserInfo): ThunkAction<void, AppState, unknown, Action> => (dispatch): void => {
  dispatch(disconnectWebsocket());
  dispatch(connectWebsocket(user));
};

interface AddListenerAction extends Action {
  type: 'WS/ADD_LISTENER';
  payload: (ev: any) => void;
}

export const addListener = (callback: (ev: any) => void): ThunkAction<void, AppState, unknown, AddListenerAction> => (dispatch): void => {
  dispatch({
    type: 'WS/ADD_LISTENER',
    payload: callback,
  });
};

interface RemoveListenerAction extends Action {
  type: 'WS/REMOVE_LISTENER';
  payload: (ev: any) => void;
}

export const removeListener = (callback: (ev: any) => void): ThunkAction<void, AppState, unknown, RemoveListenerAction> => (dispatch): void => {
  dispatch({
    type: 'WS/REMOVE_LISTENER',
    payload: callback,
  });
};

type WebsocketAction = ConnectAction | DisconnectAction | AddListenerAction | RemoveListenerAction;

/** ******************************************* */
/* Selectors                                    */
/** ******************************************* */


/** ******************************************* */
/* Reducer                                      */
/** ******************************************* */

export default (state = initialState, action: WebsocketAction): WebsocketState => {
  switch (action.type) {
    case 'WS/CONNECT':
      return {
        ...state,
        socket: action.payload,
      };
    case 'WS/DISCONNECT': {
      const newState = {
        ...state,
      };
      delete newState.socket;
      return newState;
    }
    case 'WS/REMOVE_LISTENER':
      return {
        ...state,
        listeners: state.listeners.filter((l) => l === action.payload),
      };
    case 'WS/ADD_LISTENER':
      return {
        ...state,
        listeners: state.listeners.concat(action.payload),
      };
    default:
      return state;
  }
};
