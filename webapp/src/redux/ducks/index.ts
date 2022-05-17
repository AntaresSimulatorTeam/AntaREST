import { Action, combineReducers } from "redux";
import { L } from "ts-toolbelt";
import studies from "./studies";
import auth, { logout } from "./auth";
import global from "./global";
import ui from "./ui";

const appReducer = combineReducers({
  global,
  studies,
  auth,
  ui,
});

type AppReducerType = typeof appReducer;
type AppReducerStateArg = L.Head<Parameters<AppReducerType>>;

export type AppState = ReturnType<AppReducerType>;

const rootReducer = (state: AppReducerStateArg, action: Action): AppState => {
  if (action.type === logout.toString()) {
    return appReducer(undefined, action);
  }
  return appReducer(state, action);
};

export default rootReducer;
