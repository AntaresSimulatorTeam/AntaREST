import React from 'react';
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
    overflowY: 'auto'
  },
  main: {
    backgroundColor: 'white',
    maxWidth: '800px',
    maxHeight: '800px',
    display: 'flex',
    flexFlow: 'column nowrap',
    alignItems: 'center'
  },
  titlebox:{
      height: '40px',
      width: '100%',
      display: 'flex',
      flexFlow: 'row nowrap',
      alignItems: 'center',
      backgroundColor: theme.palette.primary.main
  },
  title: {
    fontWeight: 'bold',
    color: 'white',
    marginLeft: theme.spacing(2),
    overflow: 'hidden'
  },
  content: {
      flex: '1',
      width: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'center',
      alignItems: 'center',
      overflow: 'hidden',
      padding: theme.spacing(3)
  },
  footer: {
    height: '60px',
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden'      
  },
  button: {
      margin: theme.spacing(2)
  }

}));


interface PropTypes {
    open: boolean;
    title: string;
    message: string;
    handleNo: () => void;
    handleYes: () => void;
}


const ConfirmationModal = (props: PropTypes) => {

  const { title, open, message, handleYes, handleNo} = props;
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
          <Typography >
              {message}
            </Typography>
        </div>
        <div className={classes.footer}>
            <Button variant="contained"
                    className={classes.button}
                    onClick={handleNo}>
                    {t('main:noButton')}
            </Button>
            <Button variant="contained"
                    className={classes.button}
                    color="primary" 
                    onClick={handleYes}>
                    {t('main:yesButton')}
            </Button>  
        </div>
    </Paper>
    </Fade>
</Modal>
  );
};

export default ConfirmationModal;

