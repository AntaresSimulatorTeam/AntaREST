import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import moment from 'moment';
import { JobStatus, LaunchJob, StudyMetadata } from '../../../common/types';
import { getStudyJobs } from '../../../services/api/study';
import ConfirmationModal from '../../ui/ConfirmationModal';
import StudyBlockSummaryView from './StudyBlockSummaryView';
import StudyListSummaryView from './StudyListSummaryView';

interface PropTypes {
  study: StudyMetadata;
  launchStudy: (study: StudyMetadata) => void;
  deleteStudy: (study: StudyMetadata) => void;
  importStudy: (study: StudyMetadata, withOutputs?: boolean) => void;
  archiveStudy: (study: StudyMetadata) => void;
  unarchiveStudy: (study: StudyMetadata) => void;
  listMode: boolean;
}

const StudyListElementView = (props: PropTypes) => {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { study, launchStudy, deleteStudy, importStudy, listMode, archiveStudy, unarchiveStudy } = props;
  const [lastJobStatus, setLastJobsStatus] = useState<JobStatus | undefined>();
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);

  const deleteStudyAndCloseModal = () => {
    deleteStudy(study);
    setOpenConfirmationModal(false);
  };

  useEffect(() => {
    const init = async () => {
      try {
        const jobList = await getStudyJobs(study.id);
        jobList.sort((a: LaunchJob, b: LaunchJob) =>
          (moment(a.completionDate).isAfter(moment(b.completionDate)) ? -1 : 1));
        if (jobList.length > 0) setLastJobsStatus(jobList[0].status);
      } catch (e) {
        enqueueSnackbar(t('singlestudy:failtoloadjobs'), { variant: 'error' });
      }
    };
    init();
  }, [t, enqueueSnackbar, study.id]);

  return (
    <>
      {
        listMode ? (
          <StudyListSummaryView
            study={study}
            importStudy={importStudy}
            launchStudy={launchStudy}
            lastJobStatus={lastJobStatus}
            archiveStudy={archiveStudy}
            unarchiveStudy={unarchiveStudy}
            openDeletionModal={() => setOpenConfirmationModal(true)}
          />
        ) : (
          <StudyBlockSummaryView
            study={study}
            importStudy={importStudy}
            launchStudy={launchStudy}
            lastJobStatus={lastJobStatus}
            archiveStudy={archiveStudy}
            unarchiveStudy={unarchiveStudy}
            openDeletionModal={() => setOpenConfirmationModal(true)}
          />
        )
      }
      {openConfirmationModal && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={t('studymanager:confirmdelete')}
          handleYes={deleteStudyAndCloseModal}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
    </>
  );
};

export default StudyListElementView;
