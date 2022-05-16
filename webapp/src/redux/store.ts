import { configureStore } from "@reduxjs/toolkit";
import { ThunkAction } from "redux-thunk";
import { AnyAction } from "redux";
import { addWsListeners } from "../services/utils/globalWsListeners";
import rootReducer, { AppState } from "./ducks";
import localStorageMiddleware from "./middlewares/localStorageMiddleware";
import { setLogoutInterceptor } from "../services/api/client";
import { logout } from "./ducks/auth";

const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      // TODO: fix all issue then set it to true (default value)
      immutableCheck: false,
      serializableCheck: false,
    }).prepend(localStorageMiddleware.middleware),
});

setLogoutInterceptor(() => store.dispatch(logout()));

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
