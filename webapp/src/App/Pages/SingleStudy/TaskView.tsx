import React, { useEffect, useState } from 'react';
import { makeStyles, createStyles, Theme, Paper, Typography, GridList, GridListTile } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import {getStudyJobs, LaunchJob } from '../../../services/api/study';

const useStyles = makeStyles((theme: Theme) => createStyles({
    root:{
        flex: 1,
        height: '95%',
        minWidth: '350px',
        minHeight: '250px',
        display: 'flex',
        flexFlow: 'column nowrap',
        justifyContent: 'flex-start',
        alignItems: 'center',
        backgroundColor: 'white',
        margin: theme.spacing(1),
        paddingBottom: theme.spacing(1),
        overflowY: 'auto',
        overflowX: 'hidden',
        border: `1px solid ${theme.palette.primary.main}`
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
          paddingLeft: theme.spacing(2)     
      },
      title: {
          fontWeight: 'bold',
          color: 'white'
      },
      tasksList: {
        flex: 1,
        width: '100%',
        display: 'flex',
        flexFlow: 'column nowrap',
        justifyContent: 'flex-start',
        alignItems: 'center',
        overflowX: 'hidden',
        overflowY: 'auto'        
      },
      task:
      {
        margin: theme.spacing(1),
        padding: theme.spacing(2),
        border: `1px solid ${theme.palette.primary.main}`
      },
      message: {
        margin: theme.spacing(1),
        padding: theme.spacing(2),
        color: theme.palette.primary.main  
      },
      gridList:{
        width: '100%'
      },
     gridTile: {
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      color: theme.palette.primary.main  
     },
     label:{
         fontWeight: 'bold'
     }
}));

interface PropTypes {
    studyId: string;
}

const TaskView = (props: PropTypes) => {
  const { studyId } = props;
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [jobs, setJobs] = useState<Array<LaunchJob>>([]);

  useEffect(() => {
    const init = async () => {
        try{
        const _jobs = await getStudyJobs(studyId)
        setJobs(_jobs);
        }
        catch(e)
        {
            enqueueSnackbar(t('singlestudy:failtoloadjobs'), { variant: 'error' });
        }
    }
    init();
  }, [t, enqueueSnackbar, studyId]);

  return (
    <Paper className={classes.root}>
        <div className={classes.header}>
                <Typography className={classes.title}>{t('singlestudy:currentTask')}</Typography>
        </div>
        <div className={classes.tasksList}>
            {
                jobs.length > 0 ?
                jobs.map((item,index) => {
                    return (
                        <Paper className={classes.task} key={index}>
                            <GridList cellHeight={50} className={classes.gridList}>
                                <GridListTile className={classes.gridTile}>
                                    <Typography className={classes.label}>{t('singlestudy:taskId')}</Typography>
                                    <Typography>{item.id}</Typography>
                                </GridListTile>
                                <GridListTile className={classes.gridTile}>
                                    <Typography className={classes.label}>{t('singlestudy:taskStatus')}</Typography>
                                    <Typography>{item.status}</Typography>
                                </GridListTile>
                                <GridListTile className={classes.gridTile}>
                                    <Typography className={classes.label}>{t('singlestudy:taskCreationDate')}</Typography>
                                    <Typography>{item.creationDate}</Typography>
                                </GridListTile>
                                <GridListTile className={classes.gridTile}>
                                    <Typography className={classes.label}>{t('singlestudy:taskCompletionDate')}</Typography>
                                    <Typography>{item.completionDate}</Typography>
                                </GridListTile>
                                <GridListTile className={classes.gridTile}>
                                    <Typography className={classes.label}>{t('singlestudy:taskMessage')}</Typography>
                                    <Typography>{item.msg}</Typography>
                                </GridListTile>
                                <GridListTile className={classes.gridTile}>
                                    <Typography className={classes.label}>{t('singlestudy:taskExitCode')}</Typography>
                                    <Typography>{item.exitCode}</Typography>
                                </GridListTile>
                        </GridList>           
                    </Paper>                        
                    )
                }):
                <div className={classes.message}>
                    <Typography style={{fontWeight: 'bold', fontSize: '1em'}}>{t('singlestudy:noTasks')}</Typography>
                </div>
            }
        </div>
    </Paper>
  );
};

export default TaskView;