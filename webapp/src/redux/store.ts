import { configureStore } from "@reduxjs/toolkit";
import { AnyAction } from "redux";
import { ThunkAction } from "redux-thunk";
import { throttle } from "lodash";
import { setLogoutInterceptor } from "../services/api/client";
import { addWsListeners } from "../services/utils/globalWsListeners";
import rootReducer, { AppState } from "./ducks";
import { logoutAction, persistState } from "./ducks/auth";
import { resetStudies } from "./ducks/study";

const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      // TODO: fix all issue then set it to true (default value)
      immutableCheck: false,
      serializableCheck: false,
    }),
});

setLogoutInterceptor(
  () => store.dispatch(logoutAction()),
  () => store.dispatch(resetStudies())
);

store.subscribe(
  throttle(() => {
    persistState(store.getState().auth);
  }, 1000)
);

addWsListeners(store);

export type AppDispatch = typeof store.dispatch;

export type AppThunk<ReturnType = void> = ThunkAction<
  ReturnType,
  AppState,
  unknown,
  AnyAction
>;

export default store;
