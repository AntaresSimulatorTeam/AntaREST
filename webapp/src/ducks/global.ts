import debug from 'debug';
import { v4 as uuidv4 } from 'uuid';
import { Action } from 'redux';
import { ThunkAction } from 'redux-thunk';
import { AppState } from '../App/reducers';

const logError = debug('antares:global:error');

/** ******************************************* */
/* State                                        */
/** ******************************************* */

export interface GlobalState {
  onCloseListeners: {[id: string]: (event: Event) => void};
}

const initialState: GlobalState = {
  onCloseListeners: {},
};

/** ******************************************* */
/* Actions                                      */
/** ******************************************* */

export interface AddOnCloseListenerAction extends Action {
  type: 'GLOBAL/ADD_ONCLOSE_LISTENER';
  payload: {
    id: string;
    listener: (event: Event) => void;
  };
}

const createListener = (listener: () => string) => (e: Event): string|undefined => {
  const event = e || window.event;
  try {
    const confirmMessage = listener();
    if (confirmMessage) {
      event.preventDefault();
      event.returnValue = true;
      return confirmMessage;
    }
  } catch (error) {
    logError('Failed to call listener', error);
  }
  return undefined;
};

export const addOnCloseListener = (listener: () => string): ThunkAction<string, AppState, unknown, AddOnCloseListenerAction> => (dispatch): string => {
  const listenerId = uuidv4();
  const windowListener = createListener(listener);
  window.addEventListener('beforeunload', windowListener);
  dispatch({
    type: 'GLOBAL/ADD_ONCLOSE_LISTENER',
    payload: { id: listenerId, listener: windowListener },
  });
  return listenerId;
};

export interface RemoveOnCloseListenerAction extends Action {
  type: 'GLOBAL/REMOVE_ONCLOSE_LISTENER';
  payload: string;
}

export const removeOnCloseListener = (id: string): RemoveOnCloseListenerAction => ({
  type: 'GLOBAL/REMOVE_ONCLOSE_LISTENER',
  payload: id,
});

type GlobalAction = AddOnCloseListenerAction
  | RemoveOnCloseListenerAction;

/** ******************************************* */
/* Selectors / Misc                             */
/** ******************************************* */


/** ******************************************* */
/* Reducer                                      */
/** ******************************************* */

export default (state = initialState, action: GlobalAction): GlobalState => {
  switch (action.type) {
    case 'GLOBAL/ADD_ONCLOSE_LISTENER': {
      const newOnCloseListeners = {
        ...state.onCloseListeners,
        [action.payload.id]: action.payload.listener,
      };
      return {
        ...state,
        onCloseListeners: newOnCloseListeners,
      };
    }
    case 'GLOBAL/REMOVE_ONCLOSE_LISTENER': {
      const newOnCloseListeners = state.onCloseListeners;
      if (newOnCloseListeners[action.payload]) {
        window.removeEventListener('beforeunload', newOnCloseListeners[action.payload]);
        delete newOnCloseListeners[action.payload];
      }
      return {
        ...state,
        onCloseListeners: newOnCloseListeners,
      };
    }
    default:
      return state;
  }
};
