/* eslint-disable react-hooks/exhaustive-deps */
import React, { useState, useEffect } from 'react';
import debug from 'debug';
import moment from 'moment';
import { useTranslation } from 'react-i18next';
import { createStyles, makeStyles, Theme } from '@material-ui/core';
import { useNotif } from '../../services/utils';
import MainContentLoader from '../ui/loaders/MainContentLoader';
import { TaskDTO } from '../../common/types';
import { getAllMiscRunningTasks } from '../../services/api/tasks';
import TaskView from './TaskView';
import NoContent from '../ui/NoContent';

const logError = debug('antares:studymanagement:error');

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    width: '100%',
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'auto',
    position: 'relative',
  },
  breadcrumbs: {
    backgroundColor: '#d7d7d7',
    padding: theme.spacing(1),
  },
  header: {
    borderBottom: '1px solid #d7d7d7',
  },
  content: {
    flexGrow: 1,
    overflow: 'auto',
    position: 'relative',
  },
  container: {
    display: 'flex',
    width: '100%',
    flexDirection: 'column',
    flexWrap: 'nowrap',
    padding: theme.spacing(2),
    boxSizing: 'border-box',
    justifyContent: 'space-around',
  },
  job: {
    marginLeft: theme.spacing(3),
    marginRight: theme.spacing(3),
    marginBottom: theme.spacing(1),
    width: '100%',
  },
}));

const OtherJobManagement = () => {
  const classes = useStyles();
  const [t] = useTranslation();
  const [tasks, setTasks] = useState<Array<TaskDTO>>();
  const createNotif = useNotif();
  const [loaded, setLoaded] = useState(true);

  const init = async () => {
    setLoaded(false);
    try {
      const allTasks = await getAllMiscRunningTasks();
      setTasks(allTasks);
    } catch (e) {
      logError('woops', e);
      createNotif(t('jobs:failedtoretrievejobs'), { variant: 'error' });
    } finally {
      setLoaded(true);
    }
  };

  useEffect(() => {
    init();
  }, []);

  return (
    <div className={classes.root}>
      {!loaded && <MainContentLoader />}
      {loaded && tasks && tasks.length > 0 ? (
        <div className={classes.container}>
          {tasks
            .sort((a, b) => (moment(a.completion_date_utc || a.creation_date_utc).isAfter(moment(b.completion_date_utc || b.creation_date_utc)) ? -1 : 1))
            .map((task) => (
              <TaskView task={task} />
            ))}
        </div>
      ) : <NoContent />
      }
    </div>
  );
};

export default OtherJobManagement;
