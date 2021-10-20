import { Store } from 'redux';
import { addStudies, removeStudies } from '../../ducks/study';
import { getStudyMetadata } from '../api/study';
import { StudySummary, WSEvent, WSMessage } from '../../common/types';
import { addListenerAction, refreshHandlerAction } from '../../ducks/websockets';
import { AppState } from '../../App/reducers';

const studyListener = (reduxStore: Store<AppState>) => async (ev: WSMessage) => {
  const studySummary = ev.payload as StudySummary;
  switch (ev.type) {
    case WSEvent.STUDY_CREATED:
      console.log('YES SIR - STUDY CREATED: ', studySummary.id);
      reduxStore.dispatch(addStudies([await getStudyMetadata(studySummary.id)]));
      break;
    case WSEvent.STUDY_DELETED:
      console.log('YES SIR - STUDY DELETED: ', studySummary.id);
      reduxStore.dispatch(removeStudies([studySummary.id]));
      break;
    case WSEvent.STUDY_EDITED:
      console.log('YES SIR - STUDY EDITED: ', studySummary.id);
      reduxStore.dispatch(addStudies([await getStudyMetadata(studySummary.id)]));
      break;

    default:
      break;
  }
};

export const addWsListeners = (reduxStore: Store<AppState>) => {
  /* ADD LISTENERS HERE */
  reduxStore.dispatch(addListenerAction(studyListener(reduxStore)));
  reduxStore.dispatch(refreshHandlerAction());
};

export default {};
