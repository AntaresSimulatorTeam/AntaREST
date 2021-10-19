import { addStudies, removeStudies } from '../../ducks/study';
import { getStudyMetadata } from '../api/study';
import { StudySummary, WSEvent, WSMessage } from '../../common/types';

const studyListener = async (ev: WSMessage) => {
  const studySummary = ev.payload as StudySummary;
  switch (ev.type) {
    case WSEvent.STUDY_CREATED:
      console.log('YES SIR - STUDY CREATED: ', studySummary.id);
      addStudies([await getStudyMetadata(studySummary.id)]);
      break;
    case WSEvent.STUDY_DELETED:
      console.log('YES SIR - STUDY DELETED: ', studySummary.id);
      removeStudies([studySummary.id]);
      break;
    case WSEvent.STUDY_EDITED:
      console.log('YES SIR - STUDY EDITED: ', studySummary.id);
      addStudies([await getStudyMetadata(studySummary.id)]);
      break;

    default:
      break;
  }
};

export default [studyListener];
