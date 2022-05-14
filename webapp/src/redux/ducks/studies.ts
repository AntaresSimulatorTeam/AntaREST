import {
  createAction,
  createAsyncThunk,
  createEntityAdapter,
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
import { getFavoriteStudies, getStudyVersions } from "../selectors";
import { AppAsyncThunkConfig, AppThunk } from "../store";
import { makeActionName, Status } from "../utils";

export const studiesAdapter = createEntityAdapter<StudyMetadata>({
  selectId: (study) => study.id,
});

export interface StudiesState
  extends ReturnType<typeof studiesAdapter.getInitialState> {
  status: Status;
  error?: string;
  current: string;
  scrollPosition: number;
  directory: string;
  versionList: string[];
  favorites: Array<StudyMetadata["id"]>;
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

const initialState = studiesAdapter.getInitialState({
  status: Status.Idle,
  error: null as string | null,
  current: "",
  scrollPosition: 0,
  directory: "root",
  versionList: [] as string[],
  favorites:
    loadState<Array<StudyMetadata["id"]>>(DefaultFilterKey.FAVORITE_STUDIES) ||
    [],
}) as StudiesState;

const n = makeActionName("study");

////////////////////////////////////////////////////////////////
// Action Creators
////////////////////////////////////////////////////////////////

export const setCurrentStudy = createAction<
  NonNullable<StudiesState["current"]>
>(n("SET_CURRENT"));

export const setStudyScrollPosition = createAction<
  StudiesState["scrollPosition"]
>(n("SET_SCROLL_POSITION"));

const setStudyDirectory = createAction<StudiesState["directory"]>(
  n("SET_DIRECTORY")
);

export const setFavoriteStudies = createAction<StudiesState["favorites"]>(
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

export const setStudy = createAsyncThunk<
  StudyMetadata,
  WSMessage<StudySummary>,
  AppAsyncThunkConfig
>(n("SET_STUDY"), (event) => {
  const { id } = event.payload;
  return api.getStudyMetadata(id);
});

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
  const newFavorites = currentFavorites.filter((fav) => fav !== studyId);
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
      (fav, study) => fav === study.id,
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
    const isFav = !!currentFavorites.find((fav) => fav === studyInfo.id);

    dispatch(
      setFavoriteStudies(
        isFav
          ? currentFavorites.filter((fav) => fav !== studyInfo.id)
          : [...currentFavorites, studyInfo.id.toString()]
      )
    );
  };

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(createStudy.fulfilled, studiesAdapter.addOne)
    .addCase(setStudy.fulfilled, studiesAdapter.setOne)
    .addCase(deleteStudy.fulfilled, studiesAdapter.removeOne)
    .addCase(fetchStudies.pending, (draftState) => {
      draftState.status = Status.Loading;
    })
    .addCase(fetchStudies.fulfilled, (draftState, action) => {
      draftState.status = Status.Succeeded;
      studiesAdapter.removeAll(draftState);
      studiesAdapter.addMany(draftState, action);
    })
    .addCase(fetchStudies.rejected, (draftState, action) => {
      draftState.status = Status.Failed;
      draftState.error = action.error.message;
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
