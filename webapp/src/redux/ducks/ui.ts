import { createAction, createReducer } from "@reduxjs/toolkit";
import { makeActionName } from "../utils";

export interface UIState {
  menuExtended: boolean;
  currentPage: string;
}

const initialState = {
  menuExtended: false,
  currentPage: "/",
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
    });
});
