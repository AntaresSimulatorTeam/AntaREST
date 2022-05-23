import { createListenerMiddleware, isAnyOf } from "@reduxjs/toolkit";
import { UserInfo } from "../../common/types";
import storage, { StorageKey } from "../../services/utils/localStorage";
import { AppState } from "../ducks";
import { login, logout, refresh } from "../ducks/auth";
import {
  setFavoriteStudies,
  updateStudiesFromLocalStorage,
  updateStudiesSortConf,
  updateStudyFilters,
} from "../ducks/studies";

const localStorageMiddleware = createListenerMiddleware<AppState>();

////////////////////////////////////////////////////////////////
// Auth
////////////////////////////////////////////////////////////////

localStorageMiddleware.startListening({
  matcher: isAnyOf(login.fulfilled, refresh.fulfilled, logout),
  effect: (action) => {
    const user = action.payload as UserInfo;
    if (user) {
      const { expirationDate, ...toSave } = user;
      storage.setItem(StorageKey.AuthUser, toSave);
    } else {
      storage.removeItem(StorageKey.AuthUser);
    }

    // Hydrate
    if (action.type === login.fulfilled.toString()) {
      updateStudiesFromLocalStorage({
        favorites: storage.getItem(StorageKey.StudiesFavorites),
        filters: storage.getItem(StorageKey.StudiesFilters),
        sort: storage.getItem(StorageKey.StudiesSort),
      });
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
  actionCreator: updateStudyFilters,
  effect: (action) => {
    storage.setItem(StorageKey.StudiesFilters, (prev) => ({
      ...prev,
      ...action.payload,
    }));
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

export default localStorageMiddleware;
