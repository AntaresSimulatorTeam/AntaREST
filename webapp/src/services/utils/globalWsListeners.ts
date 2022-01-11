import { Store } from 'redux';
import { addStudies, removeStudies } from '../../ducks/study';
import { getStudyMetadata } from '../api/study';
import { StudySummary, WSEvent, WSMessage } from '../../common/types';
import { addListenerAction, refreshHandlerAction } from '../../ducks/websockets';
import { AppState } from '../../App/reducers';
import { getMaintenanceStatus, getInitMessageInfo } from '.';
import { setMaintenanceMode, setMessageInfo } from '../../ducks/global';

const studyListener = (reduxStore: Store<AppState>) => async (ev: WSMessage): Promise<void> => {
  const studySummary = ev.payload as StudySummary;
  switch (ev.type) {
    case WSEvent.STUDY_CREATED:
      reduxStore.dispatch(addStudies([await getStudyMetadata(studySummary.id)]));
      break;
    case WSEvent.STUDY_DELETED:
      reduxStore.dispatch(removeStudies([studySummary.id]));
      break;
    case WSEvent.STUDY_EDITED:
      reduxStore.dispatch(addStudies([await getStudyMetadata(studySummary.id)]));
      break;

    default:
      break;
  }
};

const maintenanceListener = (reduxStore: Store<AppState>) => (ev: WSMessage): void => {
  switch (ev.type) {
    case WSEvent.MAINTENANCE_MODE:
      console.log('--------------- WS/MAINTENANCE_MODE: ', ev.payload as boolean);
      reduxStore.dispatch(setMaintenanceMode(ev.payload as boolean));
      break;
    case WSEvent.MESSAGE_INFO:
      console.log('--------------- WS/MESSAGE_INFO: ', ev.payload as string);
      reduxStore.dispatch(setMessageInfo(ev.payload as string));
      break;
    default:
      break;
  }
};

export const addWsListeners = async (reduxStore: Store<AppState>): Promise<void> => {
  /* ADD LISTENERS HERE */
  reduxStore.dispatch(addListenerAction(studyListener(reduxStore)));
  reduxStore.dispatch(addListenerAction(maintenanceListener(reduxStore)));
  reduxStore.dispatch(refreshHandlerAction());

  const initMaintenanceMode = await getMaintenanceStatus();
  reduxStore.dispatch(setMaintenanceMode(initMaintenanceMode));

  const initMessageInfo = await getInitMessageInfo();
  reduxStore.dispatch(setMessageInfo(initMessageInfo));
};

export default {};
