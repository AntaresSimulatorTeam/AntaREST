import { applyMiddleware, combineReducers, createStore, Store, CombinedState } from 'redux';
import { composeWithDevTools } from 'redux-devtools-extension';
import thunk from 'redux-thunk';
import logger from 'redux-logger';

import study, { StudyState } from '../ducks/study';
import auth, { AuthState } from '../ducks/auth';

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

  return reduxStore;
}
