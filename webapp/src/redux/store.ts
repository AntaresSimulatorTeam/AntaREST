import { configureStore } from "@reduxjs/toolkit";
import { ThunkAction } from "redux-thunk";
import { AnyAction } from "redux";
import rootReducer, { AppState } from "./ducks";
import localStorageMiddleware from "./middlewares/localStorageMiddleware";

const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoreActions: true,
      },
    }).prepend(localStorageMiddleware.middleware),
});

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
