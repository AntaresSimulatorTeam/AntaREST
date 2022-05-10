import { Action } from "redux";
import { ThunkAction } from "redux-thunk";
import { AppState } from ".";

/** ******************************************* */
/* State                                        */
/** ******************************************* */

export interface UIState {
  menuExtended: boolean;
  currentPage: string;
}

const initialState: UIState = {
  menuExtended: false,
  currentPage: "/",
};

/** ******************************************* */
/* Actions                                      */
/** ******************************************* */

export interface SetMenuExtensionStatusAction extends Action {
  type: "UI/SET_MENU_EXTENSION_STATUS";
  payload: boolean;
}

export const setMenuExtensionStatusAction = (
  status: boolean
): SetMenuExtensionStatusAction => ({
  type: "UI/SET_MENU_EXTENSION_STATUS",
  payload: status,
});

export const setMenuExtension =
  (
    status: boolean
  ): ThunkAction<void, AppState, unknown, SetMenuExtensionStatusAction> =>
  (dispatch): void => {
    dispatch(setMenuExtensionStatusAction(status));
  };

export interface SetAppPageAction extends Action {
  type: "UI/SET_APP_PAGE";
  payload: string;
}

export const setAppPage = (page: string): SetAppPageAction => ({
  type: "UI/SET_APP_PAGE",
  payload: page,
});

type UIAction = SetMenuExtensionStatusAction | SetAppPageAction;

/** ******************************************* */
/* Selectors / Misc                             */
/** ******************************************* */

/** ******************************************* */
/* Reducer                                      */
/** ******************************************* */

// eslint-disable-next-line default-param-last
export default (state = initialState, action: UIAction): UIState => {
  switch (action.type) {
    case "UI/SET_MENU_EXTENSION_STATUS": {
      return {
        ...state,
        menuExtended: action.payload,
      };
    }
    case "UI/SET_APP_PAGE": {
      return {
        ...state,
        currentPage: action.payload,
      };
    }
    default:
      return state;
  }
};
