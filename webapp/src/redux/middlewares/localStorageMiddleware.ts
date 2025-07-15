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
import storage, { StorageKey } from "../../services/utils/localStorage";
import type { UserInfo } from "../../types/types";
import type { AppState } from "../ducks";
import { login, logout, refresh } from "../ducks/auth";
import {
  setFavoriteStudies,
  updateStudiesFromLocalStorage,
  updateStudiesSortConf,
  updateStudyFilters,
  deleteStudy,
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
      storage.setItem(StorageKey.AuthUser, user);
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

localStorageMiddleware.startListening({
  actionCreator: updateStudyFilters,
  effect: (action) => {
    if (action.payload.folder !== undefined) {
      storage.setItem(StorageKey.StudiesFilters, () => ({
        folder: action.payload.folder,
      }));
    }
  },
});

localStorageMiddleware.startListening({
  actionCreator: deleteStudy.fulfilled,
  effect: (e) => {
    if ("name" in e.meta.arg) {
      const { workspace, folder } = e.meta.arg;
      const folders = storage.getItem(StorageKey.StudyTreeFolders) || [];
      const filteredFolders = folders.filter(
        (f) => !(f.workspace === workspace && f.path === folder),
      );
      // remove folder of deleted study from localStorage, otherwise we'll
      // see ghost folders in the study tree
      storage.setItem(StorageKey.StudyTreeFolders, filteredFolders);
    }
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
