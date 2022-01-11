/* eslint-disable @typescript-eslint/camelcase */
import React, { useEffect, useState } from 'react';
import { createStyles, makeStyles, Theme, Button, Typography, Modal, Fade, Paper } from '@material-ui/core';
import Backdrop from '@material-ui/core/Backdrop';
import CancelIcon from '@material-ui/icons/Cancel';
import { connect, ConnectedProps } from 'react-redux';
import { AppState } from '../reducers';
import { isUserAdmin } from '../../services/utils';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'center',
    alignItems: 'center',
    color: theme.palette.primary.main,
    // margin: theme.spacing(4),
    padding: theme.spacing(3, 1),
    // backgroundColor: 'red',
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
    // backgroundColor: 'green',
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

const connector = connect(mapState);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const MessageInfoModal = (props: PropTypes) => {
  const classes = useStyles();
  const { user, messageInfo } = props;
  const [open, setOpen] = useState(true);

  const handleClose = (): void => {
    console.log('Close Message info modal');
    setOpen(false);
  };

  useEffect(() => {
    if (messageInfo !== undefined && messageInfo !== '' && user !== undefined && !isUserAdmin(user)) setOpen(true);
    else setOpen(false);
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
            <Typography>{messageInfo}</Typography>
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
