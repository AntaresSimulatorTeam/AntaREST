import { applyMiddleware, combineReducers, createStore, Store, CombinedState } from 'redux';
import { composeWithDevTools } from 'redux-devtools-extension';
import thunk from 'redux-thunk';
import logger from 'redux-logger';
import { throttle } from 'lodash';
import study, { StudyState } from '../ducks/study';
import auth, { AuthState, logoutAction, persistState as persistAuthState } from '../ducks/auth';
import { setAxiosInterceptor } from '../services/api/client';

const reducers = combineReducers({
  study,
  auth,
});

export type AppState = CombinedState<{
  study: StudyState;
  auth: AuthState;
}>;

export default function createMainStore(): Store<AppState> {
  const reduxStore = createStore(reducers, composeWithDevTools(applyMiddleware(...[thunk, logger])));

  setAxiosInterceptor(() => reduxStore.dispatch(logoutAction()));

  reduxStore.subscribe(
    throttle(() => {
      persistAuthState(reduxStore.getState().auth);
    }, 1000),
  );

  return reduxStore;
}
