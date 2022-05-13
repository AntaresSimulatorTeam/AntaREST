import { createAction, createReducer } from "@reduxjs/toolkit";
import { makeActionName } from "../utils";

export interface GlobalState {
  maintenanceMode: boolean;
  messageInfo: string;
  taskNotificationsCount: number;
}

const initialState = {
  maintenanceMode: false,
  messageInfo: "",
  taskNotificationsCount: 0,
} as GlobalState;

const n = makeActionName("global");

////////////////////////////////////////////////////////////////
// Action Creators
////////////////////////////////////////////////////////////////

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
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder

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
