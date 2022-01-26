import React, { PropsWithChildren, useEffect, useRef, useState } from 'react';
import debug from 'debug';
import { connect, ConnectedProps } from 'react-redux';
import { Popover, makeStyles, Theme, createStyles, Paper } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import { addListener, removeListener } from '../../ducks/websockets';
import { TaskEventPayload, WSEvent, WSMessage } from '../../common/types';
import { getTask } from '../../services/api/tasks';

const logError = debug('antares:downloadbadge:error');

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      width: '300px',
      height: '100px',
    },
    container: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '300px',
      flexGrow: 1,
    },
    arrow: {
      display: 'inline-block',
      height: 0,
      width: 0,
      borderRight: '10px solid transparent',
      borderBottom: '10px solid #fff',
      borderLeft: '10px solid transparent',
    },
    content: {
      color: theme.palette.primary.main,
    },
  }));

const mapState = () => ({
});

const mapDispatch = ({
  addWsListener: addListener,
  removeWsListener: removeListener,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = PropsWithChildren<ReduxProps>;

const DownloadBadge = (props: PropTypes) => {
  const { addWsListener, removeWsListener, children } = props;
  const [t] = useTranslation();
  const classes = useStyles();
  const ref = useRef<HTMLDivElement>(null);
  const [notificationMessage, setNotificationMessage] = useState<string>();

  useEffect(() => {
    const listener = async (ev: WSMessage) => {
      if (ev.type === WSEvent.DOWNLOAD_CREATED) {
        setNotificationMessage('downloads:newDownload');
      } else if (ev.type === WSEvent.DOWNLOAD_READY) {
        setNotificationMessage('downloads:downloadReady');
      } else if (ev.type === WSEvent.TASK_ADDED) {
        const taskId = (ev.payload as TaskEventPayload).id;
        try {
          const task = await getTask(taskId);
          if (task.type === 'COPY') {
            setNotificationMessage('studymanager:studycopying');
          }
        } catch (error) {
          logError(error);
        }
      }
    };
    addWsListener(listener);
    return () => removeWsListener(listener);
  }, [addWsListener, removeWsListener]);

  useEffect(() => {
    if (notificationMessage) {
      setTimeout(() => {
        setNotificationMessage(undefined);
      }, 4000);
    }
  }, [notificationMessage]);

  return (
    <>
      <div ref={ref}>
        {children}
      </div>
      {ref.current && (
      <Popover
        id="download-badge-content"
        open={!!notificationMessage}
        anchorEl={ref.current}
        onClose={() => setNotificationMessage(undefined)}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'center',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'center',
        }}
        PaperProps={{
          style: {
            background: 'transparent',
          },
        }}
      >
        <div className={classes.root}>
          <div className={classes.arrow} />
          <Paper className={classes.container}>
            <div className={classes.content}>
              {t(notificationMessage || '')}
            </div>
          </Paper>
        </div>
      </Popover>
      )}

    </>
  );
};

export default connector(DownloadBadge);
