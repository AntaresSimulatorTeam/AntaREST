import { createListenerMiddleware } from "@reduxjs/toolkit";
import { DefaultFilterKey } from "../../common/types";
import { saveState } from "../../services/utils/localStorage";
import { setFavoriteStudies } from "../ducks/study";

const localStorageMiddleware = createListenerMiddleware();

localStorageMiddleware.startListening({
  actionCreator: setFavoriteStudies,
  effect: (action) => {
    saveState(DefaultFilterKey.FAVORITE_STUDIES, action.payload);
  },
});

export default localStorageMiddleware;
