import { createAction, createReducer } from "@reduxjs/toolkit";
import { makeActionName } from "../utils";

export interface UIState {
  menuCollapsed: boolean;
  currentPage: string;
  webSocketConnected: boolean;
  maintenanceMode: boolean;
  messageInfo: string;
  taskNotificationsCount: number;
}

const initialState = {
  menuCollapsed: false,
  currentPage: "/",
  webSocketConnected: false,
  maintenanceMode: false,
  messageInfo: "",
  taskNotificationsCount: 0,
} as UIState;

const n = makeActionName("ui");

////////////////////////////////////////////////////////////////
// Action Creators
////////////////////////////////////////////////////////////////

export const setMenuCollapse = createAction<UIState["menuCollapsed"]>(
  n("SET_MENU_COLLAPSE")
);

export const setCurrentPage = createAction<UIState["currentPage"]>(
  n("SET_CURRENT_PAGE")
);

export const setWebSocketConnected = createAction<
  UIState["webSocketConnected"]
>(n("SET_WEBSOCKET_CONNECTED"));

export const incrementTaskNotifications = createAction<
  UIState["taskNotificationsCount"] | undefined
>(n("INCREMENT_TASK_NOTIFICATIONS"));

export const resetTaskNotifications = createAction(
  n("RESET_TASK_NOTIFICATIONS")
);

export const setMessageInfo = createAction<UIState["messageInfo"]>(
  n("SET_MESSAGE_INFO")
);

export const setMaintenanceMode = createAction<UIState["maintenanceMode"]>(
  n("SET_MAINTENANCE_MODE")
);

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(setMenuCollapse, (draftState, action) => {
      draftState.menuCollapsed = action.payload;
    })
    .addCase(setCurrentPage, (draftState, action) => {
      draftState.currentPage = action.payload;
    })
    .addCase(setWebSocketConnected, (draftState, action) => {
      draftState.webSocketConnected = action.payload;
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
