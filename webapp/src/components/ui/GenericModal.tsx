import React, { PropsWithChildren } from 'react';
import { createStyles, makeStyles, Theme, Button, Paper, Typography } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import Modal from '@material-ui/core/Modal';
import Backdrop from '@material-ui/core/Backdrop';
import Fade from '@material-ui/core/Fade';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    overflowY: 'auto',
  },
  main: {
    backgroundColor: 'white',
    maxWidth: '800px',
    maxHeight: '800px',
    display: 'flex',
    flexFlow: 'column nowrap',
    alignItems: 'center',
  },
  titlebox: {
    flex: 'none',
    height: '40px',
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    alignItems: 'center',
    backgroundColor: theme.palette.primary.main,
  },
  title: {
    fontWeight: 'bold',
    color: 'white',
    marginLeft: theme.spacing(2),
    overflow: 'hidden',
  },
  content: {
    flex: '1',
    paddingLeft: theme.spacing(2),
    paddingRight: theme.spacing(2),
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    alignItems: 'center',
    overflow: 'hidden',
  },
  footer: {
    flex: 'none',
    height: '60px',
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-end',
    alignItems: 'center',
    overflow: 'hidden',
  },
  button: {
    margin: theme.spacing(2),
  },

}));

interface PropTypes {
    open: boolean;
    title: string;
    actionName?: string;
    handleClose?: () => void;
    handleAction?: () => void;
}

const GenericModal = (props: PropsWithChildren<PropTypes>) => {
  const { title, open, handleClose, actionName, handleAction, children } = props;
  const classes = useStyles();
  const [t] = useTranslation();

  const handleGlobalKeyDown = (keyboardEvent: React.KeyboardEvent<HTMLDivElement>) => {
    if (keyboardEvent.key === 'Enter' && handleAction) {
      handleAction();
    } else if (keyboardEvent.key === 'Escape' && handleClose) {
      handleClose();
    }
  };

  return (
    <Modal
      aria-labelledby="transition-modal-title"
      aria-describedby="transition-modal-description"
      className={classes.root}
      open={open}
      closeAfterTransition
      BackdropComponent={Backdrop}
      BackdropProps={{
        timeout: 500,
      }}
    >
      <Fade in={open}>
        <Paper className={classes.main} onKeyDown={handleGlobalKeyDown}>
          <div className={classes.titlebox}>
            <Typography className={classes.title}>
              {title}
            </Typography>
          </div>
          <div className={classes.content}>
            {children}
          </div>
          <div className={classes.footer}>
            {handleClose && (
            <Button
              variant="contained"
              className={classes.button}
              onClick={handleClose}
            >
              {t('settings:cancelButton')}
            </Button>
            )}
            {handleAction && (
            <Button
              variant="contained"
              className={classes.button}
              color="primary"
              onClick={handleAction}
            >
              {actionName !== undefined ? actionName : t('settings:saveButton')}
            </Button>
            )}
          </div>
        </Paper>
      </Fade>
    </Modal>
  );
};

GenericModal.defaultProps = {
  handleClose: undefined,
  handleAction: undefined,
  actionName: undefined,
};

export default GenericModal;
