import React from 'react';
import { makeStyles, createStyles, Theme, Paper, Typography, CircularProgress } from '@material-ui/core';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { TaskDTO } from '../../common/types';
import { convertUTCToLocalTime } from '../../services/utils';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    display: 'flex',
    flexDirection: 'column',
    margin: theme.spacing(1, 0),
    paddingLeft: theme.spacing(1),
    paddingRight: theme.spacing(1),
    paddingTop: theme.spacing(2),
    paddingBottom: theme.spacing(2),
  },
  jobs: {
    display: 'flex',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  logs: {
    display: 'none',
    marginTop: theme.spacing(2),
    fontSize: '.8rem',
    whiteSpace: 'pre',
    padding: theme.spacing(1),
    maxHeight: '200px',
    overflowY: 'auto',
    position: 'relative',
    minHeight: '60px',
  },
  loaderContainer: {
    height: '100%',
    width: '100%',
    position: 'relative',
  },
  titleblock: {
    flexGrow: 0.6,
    display: 'flex',
    alignItems: 'center',
    width: '60%',
  },
  title: {
    color: theme.palette.primary.main,
  },
  dot: {
    width: '0.5em',
    height: '0.5em',
    borderRadius: '50%',
    marginRight: theme.spacing(1),
  },
  dateblock: {
    color: theme.palette.grey[500],
    fontSize: '0.85em',
  },
  dateicon: {
    marginRight: '0.5em',
  },
  dateandicon: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '200px',
  },
  killButtonHide: {
    display: 'none',
  },
}));

interface Props {
  task: TaskDTO;
}

const TaskView = (props: Props) => {
  const { task } = props;
  const classes = useStyles();

  return (
    <Paper className={classes.root} elevation={1}>
      <div className={classes.jobs}>
        <div className={classes.titleblock}>
          <div style={{ marginLeft: '5px', marginRight: '10px' }}>
            {
                !task.completion_date_utc &&
                <CircularProgress color="primary" style={{ width: '18px', height: '18px' }} />
            }
          </div>
          <Typography className={classes.title}>
            {task.name}
          </Typography>
        </div>
        <div className={classes.dateandicon}>
          <div className={classes.dateblock}>
            <div>
              <FontAwesomeIcon className={classes.dateicon} icon="calendar" />
              {convertUTCToLocalTime(task.creation_date_utc)}
            </div>
            <div>
              {task.completion_date_utc && (
                <>
                  <FontAwesomeIcon className={classes.dateicon} icon="calendar-check" />
                  {convertUTCToLocalTime(task.completion_date_utc)}
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </Paper>
  );
};

export default TaskView;
