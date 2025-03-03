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

import { createAction, createReducer } from "@reduxjs/toolkit";
import { makeActionName } from "../utils";

export interface UIState {
  menuOpen: boolean;
  currentPage: string;
  webSocketConnected: boolean;
  maintenanceMode: boolean;
  messageInfo: string;
  taskNotificationsCount: number;
}

const initialState = {
  menuOpen: true,
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

export const setMenuOpen = createAction<UIState["menuOpen"]>(n("SET_MENU_OPEN"));

export const setCurrentPage = createAction<UIState["currentPage"]>(n("SET_CURRENT_PAGE"));

export const setWebSocketConnected = createAction<UIState["webSocketConnected"]>(
  n("SET_WEBSOCKET_CONNECTED"),
);

export const incrementTaskNotifications = createAction<
  UIState["taskNotificationsCount"] | undefined
>(n("INCREMENT_TASK_NOTIFICATIONS"));

export const resetTaskNotifications = createAction(n("RESET_TASK_NOTIFICATIONS"));

export const setMessageInfo = createAction<UIState["messageInfo"]>(n("SET_MESSAGE_INFO"));

export const setMaintenanceMode = createAction<UIState["maintenanceMode"]>(
  n("SET_MAINTENANCE_MODE"),
);

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(setMenuOpen, (draftState, action) => {
      draftState.menuOpen = action.payload;
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
