import { Action, AnyAction } from 'redux';
import { ThunkAction } from 'redux-thunk';
import { loadState, saveState } from '../services/utils/localStorage';
import { UserInfo } from '../common/types';
import client, { setAuth } from '../services/api/client';
import { AppState } from '../App/reducers';

/** ******************************************* */
/* State                                        */
/** ******************************************* */

export interface AuthState {
  user?: UserInfo;
}

const initialState: AuthState = {
  user: loadState('auth.user'),
};

const ref = JSON.parse(JSON.stringify(initialState));
export const persistState = (state: AuthState): void => {
  if (ref.user !== state.user) {
    saveState('auth.user', state.user);
    ref.user = state.user;
  }
};

setAuth(initialState.user?.token);

/** ******************************************* */
/* Actions                                      */
/** ******************************************* */

export interface LoginAction extends Action {
  type: 'AUTH/LOGIN';
  payload: UserInfo;
}

export const loginUser = (user: UserInfo): ThunkAction<void, AppState, unknown, LoginAction> => (dispatch): void => {
  console.log(user)
  setAuth(user.token);
  dispatch({
    type: 'AUTH/LOGIN',
    payload: user,
  });
};

export const logoutAction = (): Action => ({
  type: 'AUTH/LOGOUT',
});

type AuthAction = LoginAction | AnyAction;

/** ******************************************* */
/* Selectors                                    */
/** ******************************************* */


/** ******************************************* */
/* Reducer                                      */
/** ******************************************* */

export default (state = initialState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'AUTH/LOGIN':
      return {
        ...state,
        user: action.payload,
      };
    case 'AUTH/LOGOUT':
      return {};
    default:
      return state;
  }
};
