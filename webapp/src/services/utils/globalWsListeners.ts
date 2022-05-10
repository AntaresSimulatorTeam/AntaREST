import { AnyAction, Store } from "redux";
import { ThunkDispatch } from "redux-thunk";
import { addStudies, removeStudies } from "../../redux/ducks/study";
import { getStudyMetadata } from "../api/study";
import { StudySummary, WSEvent, WSMessage } from "../../common/types";
import {
  addListenerAction,
  refreshHandlerAction,
} from "../../redux/ducks/websockets";
import { AppState } from "../../redux/ducks";
import { isStringEmpty } from ".";
import { setMaintenanceMode, setMessageInfo } from "../../redux/ducks/global";

const studyListener =
  (reduxStore: Store<AppState>) =>
  async (ev: WSMessage): Promise<void> => {
    const studySummary = ev.payload as StudySummary;
    switch (ev.type) {
      case WSEvent.STUDY_CREATED:
        reduxStore.dispatch(
          addStudies([await getStudyMetadata(studySummary.id)])
        );
        break;
      case WSEvent.STUDY_DELETED:
        (
          reduxStore.dispatch as ThunkDispatch<
            AppState,
            Array<string>,
            AnyAction
          >
        )(removeStudies([studySummary.id]));
        break;
      case WSEvent.STUDY_EDITED:
        reduxStore.dispatch(
          addStudies([await getStudyMetadata(studySummary.id)])
        );
        break;

      default:
        break;
    }
  };

const maintenanceListener =
  (reduxStore: Store<AppState>) =>
  (ev: WSMessage): void => {
    switch (ev.type) {
      case WSEvent.MAINTENANCE_MODE:
        reduxStore.dispatch(setMaintenanceMode(ev.payload as boolean));
        break;
      case WSEvent.MESSAGE_INFO:
        reduxStore.dispatch(
          setMessageInfo(
            isStringEmpty(ev.payload as string) ? "" : (ev.payload as string)
          )
        );
        break;
      default:
        break;
    }
  };

export const addWsListeners = async (
  reduxStore: Store<AppState>
): Promise<void> => {
  /* ADD LISTENERS HERE */
  reduxStore.dispatch(addListenerAction(studyListener(reduxStore)));
  reduxStore.dispatch(addListenerAction(maintenanceListener(reduxStore)));
  reduxStore.dispatch(refreshHandlerAction());
};

export default {};
