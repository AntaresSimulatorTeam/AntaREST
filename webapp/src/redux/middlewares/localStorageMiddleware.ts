import { createListenerMiddleware, isAnyOf } from "@reduxjs/toolkit";
import { DefaultFilterKey, UserInfo } from "../../common/types";
import { saveState } from "../../services/utils/localStorage";
import { login, logout, refresh } from "../ducks/auth";
import { setFavoriteStudies } from "../ducks/studies";

const localStorageMiddleware = createListenerMiddleware();

// TODO: save data by user id
localStorageMiddleware.startListening({
  actionCreator: setFavoriteStudies,
  effect: (action) => {
    saveState(DefaultFilterKey.FAVORITE_STUDIES, action.payload);
  },
});

localStorageMiddleware.startListening({
  matcher: isAnyOf(login.fulfilled, refresh.fulfilled, logout),
  effect: (action) => {
    const user = action.payload as UserInfo;
    if (user) {
      const { expirationDate, ...toSave } = user;
      saveState("auth.user", toSave);
    } else {
      saveState("auth.user", undefined);
    }
  },
});

export default localStorageMiddleware;
