/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState, ReactNode } from 'react';
import { Paper, makeStyles, Theme, createStyles } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { Translation } from 'react-i18next';
import StudyFileView from './StudyFileView';
import StudyJsonView from './StudyJsonView';
import MainContentLoader from '../../ui/loaders/MainContentLoader';
import { getStudyData } from '../../../services/api/study';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    padding: theme.spacing(2),
    overflow: 'auto',
    flexGrow: 1,
  },
}));

interface PropTypes {
  type: 'json' | 'file';
  sid: string;
  dataref: string;
}

const StudyDataView = (props: PropTypes) => {
  const { type, sid, dataref } = props;
  const { enqueueSnackbar } = useSnackbar();
  const [view, setView] = useState<ReactNode>();
  const classes = useStyles();

  useEffect(() => {
    setView(
      <div style={{ width: '100%', height: '100%', position: 'relative' }}>
        <MainContentLoader />
      </div>,
    );
    (async () => {
      try {
        const res = await getStudyData(sid, dataref, -1);
        setView(type === 'file' ? <StudyFileView url={res} /> : <StudyJsonView data={JSON.stringify(res)} />);
      } catch (e) {
        enqueueSnackbar(<Translation>{(t) => t('studymanager:failtoretrievedata')}</Translation>, { variant: 'error' });
      }
    })();
  }, [dataref]);

  return (
    <Paper className={classes.root}>
      {view}
    </Paper>
  );
};

export default StudyDataView;
