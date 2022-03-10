import React, { PropsWithChildren } from 'react';
import { createStyles, makeStyles, Theme, Button, Paper, Typography, Box, Modal, Backdrop, Fade } from '@material-ui/core';
import { useTranslation } from 'react-i18next';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    overflowY: 'auto',
  },
  main: {
    backgroundColor: 'white',
    width: '80%',
    height: '70%',
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
    padding: theme.spacing(1),
    width: '98%',
    display: 'flex',
    flexFlow: 'column nowrap',
    alignItems: 'flex-start',
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
    handleClose: () => void;
}

const ConstraintModal = (props: PropsWithChildren<PropTypes>) => {
  const { title, open, handleClose, children } = props;
  const classes = useStyles();
  const [t] = useTranslation();

  const handleGlobalKeyDown = (keyboardEvent: React.KeyboardEvent<HTMLDivElement>) => {
    if (keyboardEvent.key === 'Escape' && handleClose) {
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
          <Box className={classes.titlebox}>
            <Typography className={classes.title}>
              {title}
            </Typography>
          </Box>
          <Box className={classes.content}>
            {children}
          </Box>
          <Box className={classes.footer}>
            {handleClose && (
            <Button
              variant="contained"
              className={classes.button}
              onClick={handleClose}
            >
              {t('settings:cancelButton')}
            </Button>
            )}
          </Box>
        </Paper>
      </Fade>
    </Modal>
  );
};

export default ConstraintModal;
