/* eslint-disable @typescript-eslint/camelcase */
import React, { useEffect, useState } from 'react';
import { createStyles, makeStyles, Theme, Button, Modal, Fade, Paper, Typography } from '@material-ui/core';
import { connect, ConnectedProps } from 'react-redux';
import { useTranslation } from 'react-i18next';
import Backdrop from '@material-ui/core/Backdrop';
import CancelIcon from '@material-ui/icons/Cancel';
import { useSnackbar } from 'notistack';
import { AxiosError } from 'axios';
import { AppState } from '../reducers';
import { isStringEmpty, isUserAdmin } from '../../services/utils';
import { getMessageInfo } from '../../services/api/maintenance';
import { setMessageInfo } from '../../ducks/global';
import enqueueErrorSnackbar from '../../components/ui/ErrorSnackBar';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'center',
    alignItems: 'center',
    color: theme.palette.primary.main,
    padding: theme.spacing(3, 1),
  },
  main: {
    position: 'relative',
    width: '600px',
    minHeight: '100px',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: theme.shape.borderRadius,
    border: `2px solid ${theme.palette.primary.main}`,
    padding: theme.spacing(3),
    outline: 0,
  },
  cancelIcon: {
    position: 'absolute',
    width: '24px',
    height: '24px',
    color: theme.palette.primary.main,
    top: '10px',
    right: '12px',
    cursor: 'pointer',
    '&:hover': {
      color: theme.palette.secondary.main,
    },
  },
  content: {
    width: '90%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: theme.spacing(3),
  },
  footer: {
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'center',
    alignItems: 'center',
  },
  button: {
    margin: theme.spacing(2),
  },
}));

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

const MessageInfoModal = (props: PropTypes) => {
  const classes = useStyles();
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
    <Modal
      aria-labelledby="transition-modal-title"
      aria-describedby="transition-modal-description"
      className={classes.root}
      open={open}
      onClose={() => setOpen(false)}
      closeAfterTransition
      BackdropComponent={Backdrop}
      BackdropProps={{
        timeout: 500,
      }}
    >
      <Fade in={open}>
        <Paper className={classes.main}>
          <div className={classes.content}>
            <Typography variant="body1" style={{ whiteSpace: 'pre-wrap' }}>{messageInfo}</Typography>
          </div>
          <div className={classes.footer}>
            <Button
              variant="contained"
              className={classes.button}
              color="primary"
              onClick={handleClose}
            >
              OK
            </Button>
          </div>
          <CancelIcon className={classes.cancelIcon} onClick={handleClose} />
        </Paper>
      </Fade>
    </Modal>
  );
};

export default connector(MessageInfoModal);
