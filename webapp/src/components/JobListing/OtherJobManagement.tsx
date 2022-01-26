/* eslint-disable react-hooks/exhaustive-deps */
import React, { useState, useEffect } from 'react';
import debug from 'debug';
import moment from 'moment';
import { useTranslation } from 'react-i18next';
import { createStyles, makeStyles, Theme } from '@material-ui/core';
import { connect, ConnectedProps } from 'react-redux';
import { useNotif } from '../../services/utils';
import MainContentLoader from '../ui/loaders/MainContentLoader';
import { TaskDTO, TaskEventPayload, WSEvent, WSMessage } from '../../common/types';
import { getAllMiscRunningTasks, getTask } from '../../services/api/tasks';
import TaskView from './TaskView';
import NoContent from '../ui/NoContent';
import { addListener, removeListener, subscribe, unsubscribe, WsChannel } from '../../ducks/websockets';

const logError = debug('antares:otherjobmanagement:error');

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

const mapState = () => ({
});

const mapDispatch = ({
  addWsListener: addListener,
  removeWsListener: removeListener,
  subscribeChannel: subscribe,
  unsubscribeChannel: unsubscribe,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const OtherJobManagement = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { addWsListener, removeWsListener, subscribeChannel, unsubscribeChannel } = props;
  const [tasks, setTasks] = useState<Array<TaskDTO>>();
  const createNotif = useNotif();
  const [loaded, setLoaded] = useState(false);

  const init = async () => {
    setLoaded(false);
    try {
      const allTasks = await getAllMiscRunningTasks();
      const dateThreshold = moment().subtract(1, 'm');
      setTasks(allTasks.filter((task) => !task.completion_date_utc || moment.utc(task.completion_date_utc).isAfter(dateThreshold)));
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

  useEffect(() => {
    const listener = async (ev: WSMessage) => {
      if (ev.type === WSEvent.TASK_COMPLETED || ev.type === WSEvent.TASK_FAILED) {
        const taskId = (ev.payload as TaskEventPayload).id;
        if (tasks?.find((task) => task.id === taskId)) {
          try {
            const updatedTask = await getTask(taskId);
            setTasks(tasks.filter((task) => task.id !== updatedTask.id).concat([updatedTask]));
          } catch (error) {
            logError(error);
          }
        }
      }
    };
    addWsListener(listener);
    return () => removeWsListener(listener);
  }, [addWsListener, removeWsListener, tasks, setTasks]);

  useEffect(() => {
    if (tasks) {
      tasks.forEach((task) => {
        subscribeChannel(WsChannel.TASK + task.id);
      });
      return () => {
        tasks.forEach((task) => {
          unsubscribeChannel(WsChannel.TASK + task.id);
        });
      };
    }
  }, [tasks, subscribeChannel, unsubscribeChannel]);

  const renderTasks = () => {
    if (tasks && tasks.length > 0) {
      return (
        <div className={classes.container}>
          {
        tasks
          .sort((a, b) => (moment(a.completion_date_utc || a.creation_date_utc).isAfter(moment(b.completion_date_utc || b.creation_date_utc)) ? -1 : 1))
          .map((task) => (
            <TaskView key={task.id} task={task} />
          ))
        }
        </div>
      );
    }
    return <NoContent />;
  };

  return (
    <div className={classes.root}>
      {!loaded && <MainContentLoader />}
      {loaded && renderTasks()}
    </div>
  );
};

export default connector(OtherJobManagement);
