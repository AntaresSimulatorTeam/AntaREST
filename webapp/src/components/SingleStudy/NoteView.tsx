/* eslint-disable jsx-a11y/no-static-element-interactions */
/* eslint-disable jsx-a11y/click-events-have-key-events */
import React, { useState } from 'react';
import { AxiosError } from 'axios';
import {
  makeStyles,
  createStyles,
  Theme,
  Paper,
  Typography,
} from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import CreateIcon from '@material-ui/icons/Create';
import enqueueErrorSnackbar from '../ui/ErrorSnackBar';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '100%',
      flex: 1,
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: 'white',
      margin: theme.spacing(1),
      overflowY: 'auto',
      overflowX: 'hidden',
    },
    header: {
      width: '100%',
      height: '40px',
      boxSizing: 'border-box',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: theme.palette.primary.main,
      paddingLeft: theme.spacing(2),
    },
    title: {
      fontWeight: 'bold',
      color: 'white',
    },
    main: {
      flex: 1,
      width: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      overflowX: 'hidden',
      overflowY: 'auto',
    },
    headerButton: {
      width: '100%',
      height: '40px',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-end',
      alignItems: 'center',
      paddingRight: theme.spacing(3),
    },
    editButton: {
      width: '20px',
      height: 'auto',
      color: theme.palette.primary.main,
      cursor: 'pointer',
      '&:hover': {
        color: theme.palette.secondary.main,
      },
    },
    content: {
      flex: 1,
      width: '100%',
    },
  }));

const TaskView = () => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();

  return (
    <Paper className={classes.root}>
      <div className={classes.header}>
        <Typography className={classes.title}>{t('singlestudy:notes')}</Typography>
      </div>
      <div className={classes.main}>
        <div className={classes.headerButton}>
          <CreateIcon className={classes.editButton} />
        </div>
        <div className={classes.content} />
      </div>
    </Paper>
  );
};

export default TaskView;
