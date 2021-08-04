import { Action } from 'redux';
import { AppState } from '../App/reducers';
import { StudyMetadata } from '../common/types';

/** ******************************************* */
/* State                                        */
/** ******************************************* */

export interface StudyState {
  current?: string;
  activeStudyInfo?: StudyMetadata;
  studies: StudyMetadata[];
}

const initialState: StudyState = {
  studies: [],
};

/** ******************************************* */
/* Actions                                      */
/** ******************************************* */

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

interface SetStudyInfoAction extends Action {
  type: 'STUDY/SET_STUDY_INFO';
  payload: StudyMetadata | undefined;
}

export const setStudyInfo = (study: StudyMetadata | undefined): SetStudyInfoAction => ({
  type: 'STUDY/SET_STUDY_INFO',
  payload: study,
});

type StudyAction = ViewStudyAction | InitStudyListAction | RemoveStudyAction | AddStudyAction | SetStudyInfoAction;

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
    case 'STUDY/SET_STUDY_INFO':
      return {
        ...state,
        activeStudyInfo: action.payload,
      };
    default:
      return state;
  }
};
