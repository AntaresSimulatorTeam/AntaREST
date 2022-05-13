import {
  createAction,
  createAsyncThunk,
  createReducer,
} from "@reduxjs/toolkit";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import {
  DefaultFilterKey,
  GenericInfo,
  StudyMetadata,
  StudyPublicMode,
  StudySummary,
  WSMessage,
} from "../../common/types";
import * as api from "../../services/api/study";
import { loadState } from "../../services/utils/localStorage";
import { getFavoriteStudies, getStudy, getStudyVersions } from "../selectors";
import { AppAsyncThunkConfig, AppThunk } from "../store";
import { makeActionName } from "../utils";

export interface StudyState {
  current?: StudyMetadata["id"];
  studies: StudyMetadata[];
  scrollPosition: number;
  directory: string;
  versionList?: string[];
  favorites: GenericInfo[];
}

type StudyCreator = {
  name: string;
  version?: string;
  groups?: string[];
  publicMode?: StudyPublicMode;
  tags?: string[];
};

type StudyUpload = {
  file: File;
  onUploadProgress?: (progress: number) => void;
};

type CreateStudyArg = StudyCreator | StudyUpload | StudyMetadata;

const initialState = {
  studies: [],
  scrollPosition: 0,
  directory: "root",
  favorites: loadState(DefaultFilterKey.FAVORITE_STUDIES) || [],
} as StudyState;

const n = makeActionName("study");

////////////////////////////////////////////////////////////////
// Action Creators
////////////////////////////////////////////////////////////////

const updateStudy = createAction<StudyMetadata>(n("UPDATE_STUDY"));

export const setCurrentStudy = createAction<NonNullable<StudyState["current"]>>(
  n("SET_CURRENT")
);

export const setStudyScrollPosition = createAction<
  StudyState["scrollPosition"]
>(n("SET_SCROLL_POSITION"));

const setStudyDirectory = createAction<StudyState["directory"]>(
  n("SET_DIRECTORY")
);

export const setFavoriteStudies = createAction<StudyState["favorites"]>(
  n("SET_FAVORITES")
);

////////////////////////////////////////////////////////////////
// Thunks
////////////////////////////////////////////////////////////////

export const createStudy = createAsyncThunk<
  StudyMetadata,
  CreateStudyArg,
  AppAsyncThunkConfig
>(n("CREATE_STUDY"), async (arg, { getState, rejectWithValue }) => {
  // StudyMetadata
  if ("id" in arg) {
    return arg;
  }

  try {
    // StudyUpload
    if ("file" in arg) {
      const { file, onUploadProgress } = arg;
      const studyId = await api.importStudy(file, onUploadProgress);
      return api.getStudyMetadata(studyId);
    }

    // StudyCreator
    const { name, version, groups, publicMode, tags } = arg;
    const state = getState();
    const versionList = getStudyVersions(state) || [];
    const studyVersion = Number(version || R.last(versionList));
    // TODO: add publicMode and tags in createStudy API to prevent multiple WebSocket trigger
    const studyId = await api.createStudy(name, studyVersion, groups);
    if (publicMode) {
      await api.changePublicMode(studyId, publicMode);
    }
    if (tags && tags.length > 0) {
      await api.updateStudyMetadata(studyId, { tags });
    }
    return api.getStudyMetadata(studyId);
  } catch (err) {
    return rejectWithValue(err);
  }
});

export const createOrUpdateStudy =
  (event: WSMessage<StudySummary>): AppThunk =>
  async (dispatch, getState) => {
    const { id } = event.payload;
    const state = getState();
    const isStudyPresent = !!getStudy(state, id);
    const studyUpToDate = await api.getStudyMetadata(id);
    const actionCreator = isStudyPresent ? updateStudy : createStudy;
    dispatch(actionCreator(studyUpToDate));
  };

export const deleteStudy = createAsyncThunk<
  StudyMetadata["id"],
  StudyMetadata["id"] | WSMessage<StudySummary>,
  AppAsyncThunkConfig
>(n("DELETE_STUDY"), async (arg, { dispatch, getState, rejectWithValue }) => {
  let studyId: string;

  if (RA.isString(arg)) {
    studyId = arg;
    try {
      await api.deleteStudy(studyId);
    } catch (err) {
      return rejectWithValue(err);
    }
  } else {
    studyId = arg.payload.id;
  }

  const state = getState();
  const currentFavorites = getFavoriteStudies(state);
  const newFavorites = currentFavorites.filter((fav) => fav.id !== studyId);
  dispatch(setFavoriteStudies(newFavorites));

  return studyId;
});

export const fetchStudies = createAsyncThunk<
  StudyMetadata[],
  undefined,
  AppAsyncThunkConfig
>(n("FETCH_STUDIES"), async (_, { dispatch, getState, rejectWithValue }) => {
  try {
    const studies = await api.getStudies();
    const state = getState();
    const currentFavorites = getFavoriteStudies(state);
    const newFavorites = R.innerJoin(
      (study, fav) => study.id === fav.id,
      currentFavorites,
      studies
    );

    if (currentFavorites.length !== newFavorites.length) {
      dispatch(setFavoriteStudies(newFavorites));
    }

    return studies;
  } catch (err) {
    return rejectWithValue(err);
  }
});

export const fetchStudyVersions = createAsyncThunk(
  n("FETCH_VERSIONS"),
  (_, { rejectWithValue }) => {
    return api.getStudyVersions().catch(rejectWithValue);
  }
);

export const toggleFavorite =
  (studyInfo: GenericInfo): AppThunk =>
  (dispatch, getState) => {
    const state = getState();
    const currentFavorites = getFavoriteStudies(state);
    const isFav = !!currentFavorites.find((fav) => fav.id === studyInfo.id);

    dispatch(
      setFavoriteStudies(
        isFav
          ? currentFavorites.filter((fav) => fav.id !== studyInfo.id)
          : [...currentFavorites, studyInfo]
      )
    );
  };

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(createStudy.fulfilled, (draftState, action) => {
      draftState.studies.push(action.payload);
    })
    .addCase(updateStudy, (draftState, action) => {
      const index = draftState.studies.findIndex(
        (study) => study.id === action.payload.id
      );
      if (index > -1) {
        draftState.studies[index] = action.payload;
      }
    })
    .addCase(deleteStudy.fulfilled, (draftState, action) => {
      draftState.studies = draftState.studies.filter(
        (study) => study.id === action.payload
      );
    })
    .addCase(fetchStudies.fulfilled, (draftState, action) => {
      draftState.studies = action.payload;
    })
    .addCase(setFavoriteStudies, (draftState, action) => {
      draftState.favorites = action.payload;
    })
    .addCase(fetchStudyVersions.fulfilled, (draftState, action) => {
      draftState.versionList = action.payload;
    })
    .addCase(setCurrentStudy, (draftState, action) => {
      draftState.current = action.payload;
    })
    .addCase(setStudyScrollPosition, (draftState, action) => {
      draftState.scrollPosition = action.payload;
    })
    .addCase(setStudyDirectory, (draftState, action) => {
      draftState.directory = action.payload;
    });
});
