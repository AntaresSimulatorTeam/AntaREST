import debug from 'debug';
import { v4 as uuidv4 } from 'uuid';
import { Action } from 'redux';
import { ThunkAction } from 'redux-thunk';
import { AppState } from './reducers';

const logError = debug('antares:ui:error');

/** ******************************************* */
/* State                                        */
/** ******************************************* */

export interface UIState {
  menuExtended: boolean;
}

const initialState: UIState = {
    menuExtended: false,
};

/** ******************************************* */
/* Actions                                      */
/** ******************************************* */

export interface SetMenuExtensionStatusAction extends Action {
  type: 'UI/SET_MENU_EXTENSION_STATUS';
  payload: boolean;
}

export const setMenuExtensionStatusAction = (status: boolean): SetMenuExtensionStatusAction => ({
    type: 'UI/SET_MENU_EXTENSION_STATUS',
    payload: status,
  });

export const setMenuExtension = (status: boolean): ThunkAction<void, AppState, unknown, SetMenuExtensionStatusAction> => (dispatch): void => {
    dispatch(setMenuExtensionStatusAction(status));
};

type UIAction = SetMenuExtensionStatusAction;

/** ******************************************* */
/* Selectors / Misc                             */
/** ******************************************* */

/** ******************************************* */
/* Reducer                                      */
/** ******************************************* */

export default (state = initialState, action: UIAction): UIState => {
  switch (action.type) {
    case 'UI/SET_MENU_EXTENSION_STATUS': {
      return {
        ...state,
        menuExtended: action.payload,
      };
    }
    default:
      return state;
  }
};
