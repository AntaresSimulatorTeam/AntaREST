import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { StudyMetadata } from '../../../common/types';
import ConfirmationModal from '../../ui/ConfirmationModal';
import StudyListSummaryView from './StudyListSummaryView';

interface PropTypes {
  study: StudyMetadata;
  launchStudy: (study: StudyMetadata) => void;
  deleteStudy: (study: StudyMetadata) => void;
  importStudy: (study: StudyMetadata, withOutputs?: boolean) => void;
  archiveStudy: (study: StudyMetadata) => void;
  unarchiveStudy: (study: StudyMetadata) => void;
}

const StudyListElementView = (props: PropTypes) => {
  const [t] = useTranslation();
  const { study, launchStudy, deleteStudy, importStudy, archiveStudy, unarchiveStudy } = props;
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);

  const deleteStudyAndCloseModal = () => {
    deleteStudy(study);
    setOpenConfirmationModal(false);
  };

  return (
    <>
      <StudyListSummaryView
        study={study}
        importStudy={importStudy}
        launchStudy={launchStudy}
        archiveStudy={archiveStudy}
        unarchiveStudy={unarchiveStudy}
        openDeletionModal={() => setOpenConfirmationModal(true)}
      />
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
