import { createOrUpdateStudy, deleteStudy } from "../../redux/ducks/study";
import { StudySummary, WSEvent, WSMessage } from "../../common/types";
import {
  addListenerAction,
  refreshHandlerAction,
} from "../../redux/ducks/websockets";
import { isStringEmpty } from ".";
import { setMaintenanceMode, setMessageInfo } from "../../redux/ducks/global";
import { AppStore } from "../../redux/store";

const studyListener =
  (reduxStore: AppStore) =>
  async (ev: WSMessage<StudySummary>): Promise<void> => {
    switch (ev.type) {
      case WSEvent.STUDY_CREATED:
      case WSEvent.STUDY_EDITED:
        reduxStore.dispatch(createOrUpdateStudy(ev));
        break;
      case WSEvent.STUDY_DELETED:
        reduxStore.dispatch(deleteStudy(ev));
        break;

      default:
        break;
    }
  };

const maintenanceListener =
  (reduxStore: AppStore) =>
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

export const addWsListeners = async (reduxStore: AppStore): Promise<void> => {
  /* ADD LISTENERS HERE */
  reduxStore.dispatch(addListenerAction(studyListener(reduxStore)));
  reduxStore.dispatch(addListenerAction(maintenanceListener(reduxStore)));
  reduxStore.dispatch(refreshHandlerAction());
};

export default {};
