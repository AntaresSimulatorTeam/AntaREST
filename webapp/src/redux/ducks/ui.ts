import { createAction, createReducer } from "@reduxjs/toolkit";
import { makeActionName } from "../utils";

export interface UIState {
  menuExtended: boolean;
  currentPage: string;
  webSocketConnected: boolean;
}

const initialState = {
  menuExtended: false,
  currentPage: "/",
  webSocketConnected: false,
} as UIState;

const n = makeActionName("ui");

////////////////////////////////////////////////////////////////
// Action Creators
////////////////////////////////////////////////////////////////

export const setMenuExtensionStatus = createAction<UIState["menuExtended"]>(
  n("SET_MENU_EXTENSION_STATUS")
);

export const setCurrentPage = createAction<UIState["currentPage"]>(
  n("SET_CURRENT_PAGE")
);

export const setWebSocketConnected = createAction<
  UIState["webSocketConnected"]
>(n("SET_WEBSOCKET_CONNECTED"));

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(setMenuExtensionStatus, (draftState, action) => {
      draftState.menuExtended = action.payload;
    })
    .addCase(setCurrentPage, (draftState, action) => {
      draftState.currentPage = action.payload;
    })
    .addCase(setWebSocketConnected, (draftState, action) => {
      draftState.webSocketConnected = action.payload;
    });
});
