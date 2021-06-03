import React from 'react';
import { createStyles, makeStyles, Theme, Typography, Paper, Button } from '@material-ui/core';
import { useTranslation } from 'react-i18next';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flex: '1',
    height: '100%',
    overflowY: 'auto',
    overflowX: 'hidden',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    padding: theme.spacing(3)
  },
  main: {
    width: '90%',
    minHeight: '200px',
    backgroundColor: 'white',
    display: 'flex',
    padding: theme.spacing(3),
    margin: theme.spacing(3),
    flexFlow: 'column nowrap',
    justifyContent: 'space-between',
    alignItems: 'center',
    color: theme.palette.primary.main,
    border: `1px solid ${theme.palette.primary.main}`
  },
  message: {
      fontSize: '1em',
      fontWeight: 'bold'
  },
  token: {
      fontSize: '0.8em',
      wordWrap: "break-word",
      width: '100%',
      margin: theme.spacing(2)
  }
}));


interface PropTypes {
    token: string;
    onButtonClick: () => void
}


const TokenPrinter = (props: PropTypes) => {

  const {token, onButtonClick } = props;
  const classes = useStyles();
  const [t] = useTranslation();

  return (
    <div className={classes.root}>
      <Paper className={classes.main}>
        <Typography variant="h2" className={classes.message}>
              {t('settings:printTokenMessage')} :    
        </Typography>
        <Typography variant="h3"
                    className={classes.token}>
            {token}  
        </Typography>
        <Button variant="contained"
                color="primary" 
                onClick={onButtonClick}>
          {t('main:backButton')}
        </Button>  
      </Paper>
    </div>
  );
};

export default TokenPrinter;