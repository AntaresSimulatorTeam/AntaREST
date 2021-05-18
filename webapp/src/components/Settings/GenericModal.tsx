import React, {PropsWithChildren} from 'react';
import { createStyles, makeStyles, Theme, Button, Paper, Typography } from '@material-ui/core';
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
    width: '50%',
    height: '50%',
    maxWidth: '500px',
    maxHeight: '500px',
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
      flexFlow: 'row nowrap',
      alignItems: 'center',
      overflow: 'hidden'
  },
  footer: {
    height: '60px',
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-end',
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
    handleClose: () => void;
    handleSave: () => void;
}


const GenericModal = (props: PropsWithChildren<PropTypes>) => {

  const { title, open, handleClose, handleSave, children } = props;
  const classes = useStyles();

  return (
    <Modal
    aria-labelledby="transition-modal-title"
    aria-describedby="transition-modal-description"
    className={classes.root}
    open={open}
    onClose={handleClose}
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
        <Button variant="contained"
                className={classes.button}
                color="primary" 
                onClick={handleSave}>
                Save
        </Button> 
        <Button variant="contained"
                className={classes.button}
                color="primary" 
                onClick={handleClose}>
                Cancel
        </Button> 
        </div>
    </Paper>
    </Fade>
</Modal>
  );
};

export default GenericModal;

