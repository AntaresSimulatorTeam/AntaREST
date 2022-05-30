import { Action, combineReducers } from "redux";
import { L } from "ts-toolbelt";
import studies from "./studies";
import users from "./users";
import groups from "./groups";
import auth, { logout } from "./auth";
import ui from "./ui";
import synthesis from "./synthesis";

const appReducer = combineReducers({
  studies,
  users,
  groups,
  auth,
  ui,
  synthesis,
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
