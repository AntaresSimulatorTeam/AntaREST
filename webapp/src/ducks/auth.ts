/* eslint-disable camelcase */
/* eslint-disable @typescript-eslint/camelcase */
import { Action } from 'redux';
import { ThunkAction } from 'redux-thunk';
import jwt_decode from 'jwt-decode';
import lodash from 'lodash';
import moment from 'moment';
import { loadState, saveState } from '../services/utils/localStorage';
import { UserInfo } from '../common/types';
import { setAuth } from '../services/api/client';
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
  const user = state.user ? { ...state.user } : undefined;
  if (user) {
    delete user.expirationDate;
  }
  if (!lodash.isEqual(ref.user, user)) {
    saveState('auth.user', user);
    ref.user = user;
  }
};

setAuth(initialState.user?.accessToken);

/** ******************************************* */
/* Actions                                      */
/** ******************************************* */

export interface LoginAction extends Action {
  type: 'AUTH/LOGIN';
  payload: UserInfo;
}

export const loginUser = (user: UserInfo): ThunkAction<void, AppState, unknown, LoginAction> => (dispatch): void => {
  const tokenData = jwt_decode(user.accessToken);
  //console.log(tokenData);
  setAuth(user.accessToken);
  dispatch({
    type: 'AUTH/LOGIN',
    payload: { ...user, expirationDate: moment.unix((tokenData as any).exp) },
  });
};

export interface LogoutAction extends Action {
  type: 'AUTH/LOGOUT';
}

export const logoutAction = (): LogoutAction => ({
  type: 'AUTH/LOGOUT',
});


type AuthAction = LoginAction | LogoutAction;

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
    case 'AUTH/LOGOUT': {
      setAuth(undefined);
      return {};
    }
    default:
      return state;
  }
};
