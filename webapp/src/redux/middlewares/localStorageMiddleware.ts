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
import { setMenuCollapse } from "../ducks/ui";

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
          filters: storage.getItem(StorageKey.StudiesFilters),
          sort: storage.getItem(StorageKey.StudiesSort),
        })
      );

      const menuCollapsed = storage.getItem(StorageKey.UIMenuCollapsed);
      if (menuCollapsed !== null) {
        dispatch(setMenuCollapse(menuCollapsed));
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

////////////////////////////////////////////////////////////////
// UI
////////////////////////////////////////////////////////////////

localStorageMiddleware.startListening({
  actionCreator: setMenuCollapse,
  effect: (action) => {
    storage.setItem(StorageKey.UIMenuCollapsed, action.payload);
  },
});

export default localStorageMiddleware;
