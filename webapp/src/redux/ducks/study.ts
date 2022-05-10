import { Action, AnyAction } from "redux";
import { ThunkAction } from "redux-thunk";
import * as R from "ramda";
import { AppState } from ".";
import {
  DefaultFilterKey,
  GenericInfo,
  StudyMetadata,
} from "../../common/types";
import { getStudyVersions } from "../../services/api/study";
import { loadState, saveState } from "../../services/utils/localStorage";

/** ******************************************* */
/* State                                        */
/** ******************************************* */

export interface StudyState {
  current?: string;
  studies: StudyMetadata[];
  scrollPosition: number;
  directory: string;
  versionList?: Array<string>;
  favorites: Array<GenericInfo>;
}

const initialState: StudyState = {
  studies: [],
  scrollPosition: 0,
  directory: "root",
  favorites: loadState(DefaultFilterKey.FAVORITE_STUDIES) || [],
};

/** ******************************************* */
/* Actions                                      */
/** ******************************************* */

interface UpdateFavoritesAction extends Action {
  type: "STUDY/UPDATE_FAVORITES";
  payload: Array<GenericInfo>;
}

export const toggleFavorite =
  (studyInfo: GenericInfo): ThunkAction<void, AppState, unknown, Action> =>
  (dispatch, getState) => {
    const { study } = getState();
    const { favorites } = study;
    const filteredFvorites = favorites.filter((f) => f.id !== studyInfo.id);
    const newFavorites = filteredFvorites.concat(
      favorites.length === filteredFvorites.length ? [studyInfo] : []
    );
    saveState(DefaultFilterKey.FAVORITE_STUDIES, newFavorites);
    dispatch({
      type: "STUDY/UPDATE_FAVORITES",
      payload: newFavorites.concat(),
    });
  };

interface UpdateScrollPositionAction extends Action {
  type: "STUDY/SCROLL_POSITION";
  payload: number;
}

export const updateScrollPosition = (
  scrollPosition: number
): UpdateScrollPositionAction => ({
  type: "STUDY/SCROLL_POSITION",
  payload: scrollPosition,
});

interface FolderPositionAction extends Action {
  type: "STUDY/FOLDER_POSITION";
  payload: string;
}

export const updateFolderPosition = (dir: string): FolderPositionAction => ({
  type: "STUDY/FOLDER_POSITION",
  payload: dir,
});

interface InitStudyListAction extends Action {
  type: "STUDY/INIT_STUDY_LIST";
  payload: StudyMetadata[];
}

export const resetStudies = (): InitStudyListAction => ({
  type: "STUDY/INIT_STUDY_LIST",
  payload: [],
});

export const initStudies =
  (studies: StudyMetadata[]): ThunkAction<void, AppState, unknown, AnyAction> =>
  (dispatch, getState) => {
    if (studies.length > 0) {
      const { study } = getState();
      const { favorites } = study;
      dispatch({
        type: "STUDY/UPDATE_FAVORITES",
        payload: R.innerJoin(
          (study, favorite) => study.id === favorite.id,
          favorites,
          studies
        ),
      });
    }
    dispatch({
      type: "STUDY/INIT_STUDY_LIST",
      payload: studies,
    });
  };

interface InitStudiesVersionAction extends Action {
  type: "STUDY/INIT_STUDIES_VERSION";
  payload: Array<string>;
}

export const initStudiesVersion =
  (): ThunkAction<void, AppState, unknown, InitStudiesVersionAction> =>
  async (dispatch): Promise<void> => {
    const versions = await getStudyVersions();
    dispatch({
      type: "STUDY/INIT_STUDIES_VERSION",
      payload: versions,
    });
  };

interface ViewStudyAction extends Action {
  type: "STUDY/VIEW_STUDY";
  payload: string;
}

export const viewStudy = (studyId: string): ViewStudyAction => ({
  type: "STUDY/VIEW_STUDY",
  payload: studyId,
});

interface RemoveStudyAction extends Action {
  type: "STUDY/REMOVE_STUDIES";
  payload: string[];
}

export const removeStudies =
  (studyIds: string[]): ThunkAction<void, AppState, unknown, AnyAction> =>
  (dispatch, getState) => {
    const { study } = getState();
    const { favorites } = study;
    dispatch({
      type: "STUDY/UPDATE_FAVORITES",
      payload: R.filter(
        (f) => studyIds.indexOf(f.id.toString()) === -1,
        favorites
      ),
    });
    dispatch({
      type: "STUDY/REMOVE_STUDIES",
      payload: studyIds,
    });
  };

interface AddStudyAction extends Action {
  type: "STUDY/ADD_STUDIES";
  payload: StudyMetadata[];
}

export const addStudies = (studies: StudyMetadata[]): AddStudyAction => ({
  type: "STUDY/ADD_STUDIES",
  payload: studies,
});

type StudyAction =
  | ViewStudyAction
  | InitStudyListAction
  | RemoveStudyAction
  | AddStudyAction
  | UpdateScrollPositionAction
  | FolderPositionAction
  | InitStudiesVersionAction
  | UpdateFavoritesAction;

/** ******************************************* */
/* Selectors                                    */
/** ******************************************* */

export const getCurrentStudy = (state: AppState): StudyMetadata | undefined =>
  state.study.studies.find((s) => s.id === state.study.current);

/** ******************************************* */
/* Reducer                                      */
/** ******************************************* */

// eslint-disable-next-line default-param-last
export default (state = initialState, action: StudyAction): StudyState => {
  switch (action.type) {
    case "STUDY/VIEW_STUDY":
      return {
        ...state,
        current: action.payload,
      };
    case "STUDY/INIT_STUDY_LIST":
      return {
        ...state,
        studies: action.payload,
      };
    case "STUDY/REMOVE_STUDIES":
      return {
        ...state,
        studies: state.studies.filter(
          (s) => action.payload.indexOf(s.id) === -1
        ),
      };
    case "STUDY/ADD_STUDIES":
      return {
        ...state,
        studies: state.studies
          .filter(
            (s) =>
              action.payload
                .map((study: StudyMetadata) => study.id)
                .indexOf(s.id) === -1
          )
          .concat(action.payload),
      };
    case "STUDY/SCROLL_POSITION":
      if (state.scrollPosition !== action.payload) {
        return {
          ...state,
          scrollPosition: action.payload,
        };
      }
      return state;
    case "STUDY/FOLDER_POSITION":
      if (state.directory !== action.payload) {
        return {
          ...state,
          directory: action.payload,
        };
      }
      return state;
    case "STUDY/INIT_STUDIES_VERSION":
      return {
        ...state,
        versionList: action.payload,
      };
    case "STUDY/UPDATE_FAVORITES":
      return {
        ...state,
        favorites: action.payload,
      };
    default:
      return state;
  }
};
