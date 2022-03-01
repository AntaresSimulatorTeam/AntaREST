import React, { useEffect, useState } from 'react';
import { Box, Typography } from '@mui/material';
import { connect, ConnectedProps } from 'react-redux';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { AxiosError } from 'axios';
import { AppState } from '../../../store/reducers';
import { isStringEmpty, isUserAdmin } from '../../../services/utils';
import { getMessageInfo } from '../../../services/api/maintenance';
import { setMessageInfo } from '../../../store/global';
import enqueueErrorSnackbar from '../../../components/common/ErrorSnackBar';
import BasicModal from '../../../components/common/BasicModal';

const mapState = (state: AppState) => ({
  user: state.auth.user,
  messageInfo: state.global.messageInfo,
});

const mapDispatch = ({
  setMessage: setMessageInfo,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

function MessageInfoModal(props: PropTypes) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { user, messageInfo, setMessage } = props;
  const [open, setOpen] = useState(false);

  const handleClose = (): void => {
    setOpen(false);
  };

  useEffect(() => {
    const init = async () => {
      try {
        const tmpMessage = await getMessageInfo();
        setMessage(isStringEmpty(tmpMessage) ? '' : tmpMessage);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('main:onGetMessageInfoError'), e as AxiosError);
      }
    };
    init();
  }, [enqueueSnackbar, setMessage, t]);

  useEffect(() => {
    if (messageInfo !== undefined && messageInfo !== '' && (user === undefined || !isUserAdmin(user))) setOpen(true);
  }, [messageInfo, user]);

  return (
    <BasicModal
      title={t('main:logout')}
      open={open}
      onClose={() => setOpen(false)}
      closeButtonLabel={t('main:noButton')}
      rootStyle={{ width: '600px', height: '200px', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', alignItems: 'center', boxSizing: 'border-box' }}
    >
      <Box width="90%" height="100%" display="flex" flexDirection="column" justifyContent="center" alignItems="center" p={2} mb={3} boxSizing="border-box">
        <Typography variant="body1" style={{ whiteSpace: 'pre-wrap' }}>{messageInfo}</Typography>
      </Box>
    </BasicModal>
  );
}

export default connector(MessageInfoModal);
