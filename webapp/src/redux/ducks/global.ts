import { createAction, createReducer } from "@reduxjs/toolkit";
import debug from "debug";
import { v4 as uuidv4 } from "uuid";
import { getOnCloseListener } from "../selectors";
import { AppThunk } from "../store";
import { makeActionName } from "../utils";

export type OnCloseListenerIdType = string;
export type OnCloseListenerType = (event: Event) => void;

export interface GlobalState {
  onCloseListeners: { [id: OnCloseListenerIdType]: OnCloseListenerType };
  maintenanceMode: boolean;
  messageInfo: string;
  taskNotificationsCount: number;
}

const initialState = {
  onCloseListeners: {},
  maintenanceMode: false,
  messageInfo: "",
  taskNotificationsCount: 0,
} as GlobalState;

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

const n = makeActionName("global");

const logError = debug("antares:global:error");

const createListener = (fn: () => string) => {
  return (e: Event): string | undefined => {
    const event = e || window.event;
    try {
      const confirmMessage = fn();
      if (confirmMessage) {
        event.preventDefault();
        event.returnValue = true;
        return confirmMessage;
      }
    } catch (error) {
      logError("Failed to call listener", error);
    }
    return undefined;
  };
};

////////////////////////////////////////////////////////////////
// Action Creators
////////////////////////////////////////////////////////////////

const createOnCloseListener = createAction(
  n("CREATE_ONCLOSE_LISTENER"),
  (listener: OnCloseListenerType) => ({ payload: { id: uuidv4(), listener } })
);

const deleteOnCloseListener = createAction<OnCloseListenerIdType>(
  n("DELETE_ONCLOSE_LISTENER")
);

export const incrementTaskNotifications = createAction<
  GlobalState["taskNotificationsCount"] | undefined
>(n("INCREMENT_TASK_NOTIFICATIONS"));

export const resetTaskNotifications = createAction(
  n("RESET_TASK_NOTIFICATIONS")
);

export const setMessageInfo = createAction<GlobalState["messageInfo"]>(
  n("SET_MESSAGE_INFO")
);

export const setMaintenanceMode = createAction<GlobalState["maintenanceMode"]>(
  n("SET_MAINTENANCE_MODE")
);

////////////////////////////////////////////////////////////////
// Thunks
////////////////////////////////////////////////////////////////

export const createAndInitOnCloseListener =
  (fn: () => string): AppThunk<OnCloseListenerIdType> =>
  (dispatch) => {
    const listener = createListener(fn);
    const res = dispatch(createOnCloseListener(listener));
    window.addEventListener("beforeunload", listener);

    return res.payload.id;
  };

export const deleteAndClearOnCloseListener =
  (id: OnCloseListenerIdType): AppThunk =>
  (dispatch, getState) => {
    const listener = getOnCloseListener(getState(), id);
    if (listener) {
      dispatch(deleteOnCloseListener(id));
      window.removeEventListener("beforeunload", listener);
    }
  };

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(createOnCloseListener, (draftState, action) => {
      const { id, listener } = action.payload;
      draftState.onCloseListeners[id] = listener;
    })
    .addCase(deleteOnCloseListener, (draftState, action) => {
      delete draftState.onCloseListeners[action.payload];
    })
    .addCase(incrementTaskNotifications, (draftState, action) => {
      const value = action.payload ?? 1;
      if (value > 0) {
        draftState.taskNotificationsCount += value;
      }
    })
    .addCase(resetTaskNotifications, (draftState) => {
      draftState.taskNotificationsCount = 0;
    })
    .addCase(setMessageInfo, (draftState, action) => {
      draftState.messageInfo = action.payload;
    })
    .addCase(setMaintenanceMode, (draftState, action) => {
      draftState.maintenanceMode = action.payload;
    });
});
