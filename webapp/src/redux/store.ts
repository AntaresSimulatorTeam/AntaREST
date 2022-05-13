import { configureStore } from "@reduxjs/toolkit";
import { throttle } from "lodash";
import { ThunkAction } from "redux-thunk";
import { AnyAction } from "redux";
import { setLogoutInterceptor } from "../services/api/client";
import { addWsListeners } from "../services/utils/globalWsListeners";
import rootReducer, { AppState } from "./ducks";
import { logoutAction, persistState } from "./ducks/auth";
import localStorageMiddleware from "./middlewares/localStorageMiddleware";

const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      // TODO: fix all issue then set it to true (default value)
      immutableCheck: false,
      serializableCheck: false,
    }).prepend(localStorageMiddleware.middleware),
});

setLogoutInterceptor(
  () => store.dispatch(logoutAction())
  // TODO: to include in logout thunk
  // () => store.dispatch(fetchStudies([]))
);

store.subscribe(
  throttle(() => {
    persistState(store.getState().auth);
  }, 1000)
);

addWsListeners(store);

export type AppStore = typeof store;

export type AppDispatch = typeof store.dispatch;

export type AppThunk<ReturnType = void> = ThunkAction<
  ReturnType,
  AppState,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  any, // TODO: issue with unknown
  AnyAction
>;

export type AppAsyncThunkConfig = {
  state: AppState;
  dispatch: AppDispatch;
};

export default store;
