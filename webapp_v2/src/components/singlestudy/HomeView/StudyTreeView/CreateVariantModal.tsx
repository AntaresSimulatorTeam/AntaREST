import React, { useState } from 'react';
import debug from 'debug';
import { useSnackbar } from 'notistack';
import { useNavigate } from 'react-router';
import { Box } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { AxiosError } from 'axios';
import { connect, ConnectedProps } from 'react-redux';
import BasicModal from '../../../common/BasicModal';
import { AppState } from '../../../../store/reducers';
import FilledTextInput from '../../../common/FilledTextInput';
import { StudyMetadata } from '../../../../common/types';
import { addStudies } from '../../../../store/study';
import enqueueErrorSnackbar from '../../../common/ErrorSnackBar';
import { scrollbarStyle } from '../../../../theme';
import { createVariant } from '../../../../services/api/variant';

const logErr = debug('antares:createstudyform:error');

const mapState = (state: AppState) => ({
});

const mapDispatch = ({
  addStudy: (study: StudyMetadata) => addStudies([study]),
});

const connector = connect(mapState, mapDispatch);
  type PropsFromRedux = ConnectedProps<typeof connector>;
  interface OwnProps {
    open: boolean;
    parentId: string;
    onClose: () => void;
  }
  type PropTypes = PropsFromRedux & OwnProps;

function CreateVariantModal(props: PropTypes) {
  const [t] = useTranslation();
  const { open, parentId, addStudy, onClose } = props;
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [studyName, setStudyName] = useState<string>('');

  const onSave = async () => {
    if (!studyName) {
      enqueueSnackbar(t('variants:nameEmptyError'), { variant: 'error' });
      return;
    }
    try {
      const newId = await createVariant(parentId, studyName);
      setStudyName('');
      onClose();
      navigate(`/studies/${newId}`);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('variants:onVariantCreationError'), e as AxiosError);
    }
  };

  return (
    <BasicModal
      title={t('studymanager:createNewStudy')}
      open={open}
      onClose={onClose}
      closeButtonLabel={t('main:cancelButton')}
      actionButtonLabel={t('main:create')}
      onActionButtonClick={onSave}
      rootStyle={{ width: '600px', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', alignItems: 'center', boxSizing: 'border-box' }}
    >
      <Box width="100%" height="100px" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="center" p={2} boxSizing="border-box" sx={{ overflowX: 'hidden', overflowY: 'auto', ...scrollbarStyle }}>
        <Box width="100%" display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center" boxSizing="border-box">
          <FilledTextInput
            label={`${t('variants:newVariant')} *`}
            value={studyName}
            onChange={setStudyName}
            sx={{ flexGrow: 1, mr: 2 }}
          />
        </Box>
      </Box>
    </BasicModal>
  );
}

export default connector(CreateVariantModal);
