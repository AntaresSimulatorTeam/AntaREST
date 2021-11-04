import { Action } from 'redux';
import { AppState } from '../App/reducers';
import { StudyMetadata } from '../common/types';

/** ******************************************* */
/* State                                        */
/** ******************************************* */

interface ScrollPosition {
  rowIndex: number;
  columnIndex: number;
}

export interface StudyState {
  current?: string;
  studies: StudyMetadata[];
  scrollPosition: ScrollPosition;
}

const initialState: StudyState = {
  studies: [],
  scrollPosition: { rowIndex: 0, columnIndex: 0 },
};

/** ******************************************* */
/* Actions                                      */
/** ******************************************* */

interface UpdateScrollPositionAction extends Action {
  type: 'STUDY/SCROLL_POSITION';
  payload: ScrollPosition;
}

export const updateScrollPosition = (scrollPosition: ScrollPosition): UpdateScrollPositionAction => ({
  type: 'STUDY/SCROLL_POSITION',
  payload: scrollPosition,
});

interface InitStudyListAction extends Action {
  type: 'STUDY/INIT_STUDY_LIST';
  payload: StudyMetadata[];
}

export const initStudies = (studies: StudyMetadata[]): InitStudyListAction => ({
  type: 'STUDY/INIT_STUDY_LIST',
  payload: studies,
});

interface ViewStudyAction extends Action {
  type: 'STUDY/VIEW_STUDY';
  payload: string;
}

export const viewStudy = (studyId: string): ViewStudyAction => ({
  type: 'STUDY/VIEW_STUDY',
  payload: studyId,
});

interface RemoveStudyAction extends Action {
  type: 'STUDY/REMOVE_STUDIES';
  payload: string[];
}

export const removeStudies = (studyIds: string[]): RemoveStudyAction => ({
  type: 'STUDY/REMOVE_STUDIES',
  payload: studyIds,
});

interface AddStudyAction extends Action {
  type: 'STUDY/ADD_STUDIES';
  payload: StudyMetadata[];
}

export const addStudies = (studies: StudyMetadata[]): AddStudyAction => ({
  type: 'STUDY/ADD_STUDIES',
  payload: studies,
});

type StudyAction = ViewStudyAction | InitStudyListAction | RemoveStudyAction | AddStudyAction | UpdateScrollPositionAction;

/** ******************************************* */
/* Selectors                                    */
/** ******************************************* */

export const getCurrentStudy = (state: AppState): StudyMetadata | undefined => state.study.studies.find((s) => s.id === state.study.current);

/** ******************************************* */
/* Reducer                                      */
/** ******************************************* */

export default (state = initialState, action: StudyAction): StudyState => {
  switch (action.type) {
    case 'STUDY/VIEW_STUDY':
      return {
        ...state,
        current: action.payload,
      };
    case 'STUDY/INIT_STUDY_LIST':
      return {
        ...state,
        studies: action.payload,
      };
    case 'STUDY/REMOVE_STUDIES':
      return {
        ...state,
        studies: state.studies.filter((s) => action.payload.indexOf(s.id) === -1),
      };
    case 'STUDY/ADD_STUDIES':
      return {
        ...state,
        studies: state.studies.filter((s) => action.payload.map((study) => study.id).indexOf(s.id) === -1).concat(action.payload),
      };
    case 'STUDY/SCROLL_POSITION':
      if (state.scrollPosition.rowIndex !== action.payload.rowIndex) {
        return {
          ...state,
          scrollPosition: action.payload,
        };
      }
      return state;
    default:
      return state;
  }
};
