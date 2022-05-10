import {
  applyMiddleware,
  combineReducers,
  createStore,
  Store,
  CombinedState,
} from "redux";
import { composeWithDevTools } from "redux-devtools-extension";
import thunk from "redux-thunk";
import { throttle } from "lodash";
import study, { StudyState, resetStudies } from "./study";
import auth, {
  AuthState,
  logoutAction,
  persistState as persistAuthState,
} from "./auth";
import { setLogoutInterceptor } from "../../services/api/client";
import upload, { UploadState } from "./upload";
import global, { GlobalState } from "./global";
import ui, { UIState } from "./ui";
import websockets, { WebsocketState } from "./websockets";

const reducers = combineReducers({
  global,
  study,
  auth,
  upload,
  ui,
  websockets,
});

export type AppState = CombinedState<{
  global: GlobalState;
  study: StudyState;
  auth: AuthState;
  upload: UploadState;
  ui: UIState;
  websockets: WebsocketState;
}>;

export default function createMainStore(): Store<AppState> {
  const reduxStore = createStore(
    reducers,
    composeWithDevTools(applyMiddleware(thunk))
  );
  setLogoutInterceptor(
    () => reduxStore.dispatch(logoutAction()),
    () => reduxStore.dispatch(resetStudies())
  );
  reduxStore.subscribe(
    throttle(() => {
      persistAuthState(reduxStore.getState().auth);
    }, 1000)
  );

  return reduxStore;
}
