import { createAction, createReducer, PrepareAction } from "@reduxjs/toolkit";
import { v4 as uuidv4 } from "uuid";
import { AppThunk } from "../store";
import { makeActionName } from "../utils";
import {
  createAndInitOnCloseListener,
  deleteAndClearOnCloseListener,
} from "./global";

export interface UploadItem {
  id: string;
  name: string;
  completion: number;
}

type UploadItemEdit = Partial<UploadItem> & { id: UploadItem["id"] };

export interface UploadState {
  uploads: UploadItem[];
  onWindowCloseListenerId?: string;
}

const initialState = {
  uploads: [],
} as UploadState;

const n = makeActionName("upload");

////////////////////////////////////////////////////////////////
// Action Creators
////////////////////////////////////////////////////////////////

const createUpload = createAction<PrepareAction<UploadItem>>(
  n("CREATE_UPLOAD"),
  (name: UploadItem["name"]) => ({
    payload: { id: uuidv4(), name, completion: 0 },
  })
);

export const updateUpload = createAction<UploadItemEdit>(n("UPDATE_UPLOAD"));

const deleteUpload = createAction<UploadItem["id"]>(n("DELETE_UPLOAD"));

const updateOnWindowCloseListenerId = createAction<
  UploadState["onWindowCloseListenerId"]
>(n("UPDATE_GLOBAL_LISTENER"));

////////////////////////////////////////////////////////////////
// Thunks
////////////////////////////////////////////////////////////////

export const createUploadWithListener =
  (name: UploadItem["name"]): AppThunk<UploadItem["id"]> =>
  (dispatch) => {
    const res = dispatch(createUpload(name));
    const listenerId = dispatch(
      createAndInitOnCloseListener(() => "You must refresh false")
    );
    dispatch(updateOnWindowCloseListenerId(listenerId));

    return res.payload.id;
  };

export const deleteUploadWithListener =
  (id: UploadItem["id"]): AppThunk =>
  (dispatch, getState) => {
    const { upload } = getState();
    if (
      upload.uploads.length === 1 &&
      !!upload.uploads.find((upload) => upload.id === id) &&
      upload.onWindowCloseListenerId
    ) {
      dispatch(deleteAndClearOnCloseListener(upload.onWindowCloseListenerId));
    }

    dispatch(deleteUpload(id));
  };

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(createUpload, (draftState, action) => {
      draftState.uploads.push(action.payload);
    })
    .addCase(updateUpload, (draftState, action) => {
      const { id, ...newValues } = action.payload;
      const index = draftState.uploads.findIndex((upload) => upload.id === id);
      if (index > -1) {
        draftState.uploads[index] = {
          ...draftState.uploads[index],
          ...newValues,
        };
      }
    })
    .addCase(deleteUpload, (draftState, action) => {
      const index = draftState.uploads.findIndex(
        (upload) => upload.id === action.payload
      );
      if (index > -1) {
        draftState.uploads.splice(index, 1);
      }
    })
    .addCase(updateOnWindowCloseListenerId, (draftState, action) => {
      if (action.payload) {
        draftState.onWindowCloseListenerId = action.payload;
      } else {
        delete draftState.onWindowCloseListenerId;
      }
    });
});
