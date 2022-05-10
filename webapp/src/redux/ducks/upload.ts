import { Action, AnyAction } from "redux";
import { ThunkAction } from "redux-thunk";
import { v4 as uuidv4 } from "uuid";
import { AppState } from ".";
import { addOnCloseListener, removeOnCloseListener } from "./global";

/** ******************************************* */
/* State                                        */
/** ******************************************* */

export interface UploadItem {
  id: string;
  name: string;
  completion: number;
}

export interface UploadState {
  uploads: UploadItem[];
  onWindowCloseListenerId?: string;
}

const initialState: UploadState = {
  uploads: [],
};

/** ******************************************* */
/* Actions                                      */
/** ******************************************* */

export interface UploadGlobalListenerAction extends Action {
  type: "UPLOAD/UPDATE_GLOBAL_LISTENER";
  payload?: string;
}

export interface AddUploadAction extends Action {
  type: "UPLOAD/ADD";
  payload: UploadItem;
}

export const addUpload =
  (name: string): ThunkAction<string, AppState, unknown, AnyAction> =>
  (dispatch): string => {
    const uploadId = uuidv4();
    const listenerId = dispatch(
      addOnCloseListener(() => "You must refresh false")
    );
    dispatch({
      type: "UPLOAD/UPDATE_GLOBAL_LISTENER",
      payload: listenerId,
    });
    dispatch({
      type: "UPLOAD/ADD",
      payload: { id: uploadId, name, completion: 0 },
    });
    return uploadId;
  };

export interface UpdateUploadAction extends Action {
  type: "UPLOAD/UPDATE";
  payload: {
    id: string;
    completion: number;
  };
}

export const updateUpload = (
  id: string,
  completion: number
): UpdateUploadAction => ({
  type: "UPLOAD/UPDATE",
  payload: { id, completion },
});

export interface CompleteUploadAction extends Action {
  type: "UPLOAD/COMPLETE";
  payload: string;
}

export const completeUpload =
  (id: string): ThunkAction<void, AppState, unknown, AnyAction> =>
  (dispatch, getState): void => {
    const { upload } = getState();
    if (
      upload.uploads.length === 1 &&
      !!upload.uploads.find((el) => el.id === id) &&
      upload.onWindowCloseListenerId
    ) {
      dispatch(removeOnCloseListener(upload.onWindowCloseListenerId));
    }
    dispatch({
      type: "UPLOAD/COMPLETE",
      payload: id,
    });
  };

type UploadAction =
  | AddUploadAction
  | UpdateUploadAction
  | CompleteUploadAction
  | UploadGlobalListenerAction;

/** ******************************************* */
/* Selectors / Misc                             */
/** ******************************************* */

/** ******************************************* */
/* Reducer                                      */
/** ******************************************* */

// eslint-disable-next-line default-param-last
export default (state = initialState, action: UploadAction): UploadState => {
  switch (action.type) {
    case "UPLOAD/ADD":
      return {
        ...state,
        uploads: state.uploads.concat(action.payload),
      };
    case "UPLOAD/UPDATE": {
      const upload = state.uploads.find((u) => u.id === action.payload.id);
      if (upload) {
        upload.completion = action.payload.completion;
        return {
          ...state,
          uploads: state.uploads
            .filter((u) => u.id !== action.payload.id)
            .concat(upload),
        };
      }
      return state;
    }
    case "UPLOAD/COMPLETE": {
      const newState: UploadState = {
        ...state,
        uploads: state.uploads.filter((u) => u.id !== action.payload),
      };
      return newState;
    }
    case "UPLOAD/UPDATE_GLOBAL_LISTENER": {
      const newState: UploadState = { ...state };
      if (action.payload) {
        newState.onWindowCloseListenerId = action.payload;
      } else {
        delete newState.onWindowCloseListenerId;
      }
      return newState;
    }
    default:
      return state;
  }
};
