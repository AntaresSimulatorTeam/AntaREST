import { applyMiddleware, combineReducers, createStore, Store, CombinedState } from 'redux';
import { composeWithDevTools } from 'redux-devtools-extension';
import thunk from 'redux-thunk';
import logger from 'redux-logger';
import { throttle } from 'lodash';
import study, { StudyState } from '../ducks/study';
import auth, { AuthState, logoutAction, persistState as persistAuthState } from '../ducks/auth';
import { setLogoutInterceptor } from '../services/api/client';
import upload, { UploadState } from '../ducks/upload';
import global, { GlobalState } from '../ducks/global';
import websockets, { WebsocketState } from '../ducks/websockets';

const reducers = combineReducers({
  global,
  study,
  auth,
  upload,
  websockets,
});

export type AppState = CombinedState<{
  global: GlobalState;
  study: StudyState;
  auth: AuthState;
  upload: UploadState;
  websockets: WebsocketState;
}>;

export default function createMainStore(): Store<AppState> {
  const reduxStore = createStore(reducers, composeWithDevTools(applyMiddleware(...[thunk, logger])));

  setLogoutInterceptor(() => reduxStore.dispatch(logoutAction()));

  reduxStore.subscribe(
    throttle(() => {
      persistAuthState(reduxStore.getState().auth);
    }, 1000),
  );

  return reduxStore;
}
