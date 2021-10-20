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
    buttonTitle: string;
    handleClose?: () => void;
    handleAction?: () => void;
}

const GenericModal = (props: PropsWithChildren<PropTypes>) => {
  const { title, open, buttonTitle, handleClose, handleAction, children } = props;
  const classes = useStyles();
  const [t] = useTranslation();

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
        <Paper className={classes.main}>
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
              {buttonTitle}
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
};

export default GenericModal;
