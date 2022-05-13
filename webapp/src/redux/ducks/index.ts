import { combineReducers } from "redux";
import study from "./study";
import auth from "./auth";
import global from "./global";
import ui from "./ui";
import websockets from "./websockets";

const rootReducer = combineReducers({
  global,
  study,
  auth,
  ui,
  websockets,
});

export type AppState = ReturnType<typeof rootReducer>;

export default rootReducer;
