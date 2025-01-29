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

import { createListenerMiddleware, isAnyOf } from "@reduxjs/toolkit";
import type { UserInfo } from "../../types/types";
import storage, { StorageKey } from "../../services/utils/localStorage";
import type { AppState } from "../ducks";
import { login, logout, refresh } from "../ducks/auth";
import {
  setFavoriteStudies,
  updateStudiesFromLocalStorage,
  updateStudiesSortConf,
} from "../ducks/studies";
import { setMenuOpen } from "../ducks/ui";

const localStorageMiddleware = createListenerMiddleware<AppState>();

////////////////////////////////////////////////////////////////
// Auth
////////////////////////////////////////////////////////////////

localStorageMiddleware.startListening({
  matcher: isAnyOf(login.fulfilled, refresh.fulfilled, logout),
  effect: (action, { dispatch }) => {
    const user = action.payload as UserInfo;
    if (user) {
      const { expirationDate, ...toSave } = user;
      storage.setItem(StorageKey.AuthUser, toSave);
    } else {
      storage.removeItem(StorageKey.AuthUser);
    }

    // Hydrate
    if (action.type === login.fulfilled.toString()) {
      dispatch(
        updateStudiesFromLocalStorage({
          favorites: storage.getItem(StorageKey.StudiesFavorites),
          sort: storage.getItem(StorageKey.StudiesSort),
        }),
      );

      const menuCollapsed = storage.getItem(StorageKey.UIMenuCollapsed);
      if (menuCollapsed !== null) {
        dispatch(setMenuOpen(menuCollapsed));
      }
    }
  },
});

////////////////////////////////////////////////////////////////
// Studies
////////////////////////////////////////////////////////////////

localStorageMiddleware.startListening({
  actionCreator: setFavoriteStudies,
  effect: (action) => {
    storage.setItem(StorageKey.StudiesFavorites, action.payload);
  },
});

localStorageMiddleware.startListening({
  actionCreator: updateStudiesSortConf,
  effect: (action) => {
    storage.setItem(StorageKey.StudiesSort, (prev) => ({
      ...prev,
      ...action.payload,
    }));
  },
});

////////////////////////////////////////////////////////////////
// UI
////////////////////////////////////////////////////////////////

localStorageMiddleware.startListening({
  actionCreator: setMenuOpen,
  effect: (action) => {
    storage.setItem(StorageKey.UIMenuCollapsed, action.payload);
  },
});

export default localStorageMiddleware;
