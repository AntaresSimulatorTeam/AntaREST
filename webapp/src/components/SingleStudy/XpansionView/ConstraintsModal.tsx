import React from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  Modal,
  Fade,
  Paper,
  Typography,
  Button,
} from '@material-ui/core';
import Backdrop from '@material-ui/core/Backdrop';
import { useTranslation } from 'react-i18next';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
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
      padding: theme.spacing(2),
      width: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      alignItems: 'center',
      overflow: 'hidden',
      '&> code': {
        paddingLeft: theme.spacing(2),
        paddingRight: theme.spacing(2),
      },
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

interface PropType {
    open: boolean;
    title: string;
    content: string;
    onClose: () => void;
}

const ConstraintsModal = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { open, title, content, onClose } = props;

  const handleGlobalKeyDown = (keyboardEvent: React.KeyboardEvent<HTMLDivElement>) => {
    if (keyboardEvent.key === 'Escape' && onClose) {
      onClose();
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
            <code>{content}</code>
          </div>
          <div className={classes.footer}>
            {onClose && (
            <Button
              variant="contained"
              className={classes.button}
              onClick={onClose}
            >
              {t('settings:cancelButton')}
            </Button>
            )}
          </div>
        </Paper>
      </Fade>
    </Modal>
  );
};

export default ConstraintsModal;
