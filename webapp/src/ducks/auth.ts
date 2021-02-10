import { Action, AnyAction } from 'redux';

/** ******************************************* */
/* State                                        */
/** ******************************************* */

export interface AuthState {
  user?: string;
  token?: string;
}

const initialState: AuthState = {
};

/** ******************************************* */
/* Actions                                      */
/** ******************************************* */

export interface LoginAction extends Action {
  type: 'AUTH/LOGIN';
  payload: {
    user: string;
    token: string;
  };
}

export const loginUser = (userInfo: {user: string; token: string}): LoginAction => ({
  type: 'AUTH/LOGIN',
  payload: userInfo,
});

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
        ...action.payload,
        ...state,
      };
    case 'AUTH/LOGOUT':
      return {};
    default:
      return state;
  }
};
