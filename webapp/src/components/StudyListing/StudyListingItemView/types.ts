import { StudyMetadata } from '../../../common/types';

export interface StudyListingItemPropTypes {
  study: StudyMetadata;
  launchStudy: (study: StudyMetadata) => void;
  importStudy: (study: StudyMetadata, withOutputs?: boolean) => void;
  archiveStudy: (study: StudyMetadata) => void;
  unarchiveStudy: (study: StudyMetadata) => void;
  openDeletionModal: () => void;
  lastJobStatus?: 'JobStatus.RUNNING' | 'JobStatus.PENDING' | 'JobStatus.SUCCESS' | 'JobStatus.FAILED';
}
