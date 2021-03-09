import React, { useEffect, useState, useCallback } from 'react';
import debug from 'debug';
import { useSnackbar } from 'notistack';
import { makeStyles, createStyles, Theme } from '@material-ui/core';
import { Translation } from 'react-i18next';
import { getStudyData } from '../../services/api/study';
import StudyTreeView from './StudyTreeView';
import StudyDataView from './StudyDataView';
import MainContentLoader from '../ui/loaders/MainContentLoader';

const logError = debug('antares:studyview:error');

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    display: 'flex',
    width: '100%',
    overflow: 'hidden',
    flexGrow: 1,
    position: 'relative',
  },
  sidebar: {
    height: '100%',
    flex: '30% 0 0',
    overflow: 'auto',
  },
  sidebarcontent: {
    padding: theme.spacing(1),
  },
  main: {
    flexGrow: 1,
    height: '100%',
    overflow: 'hidden',
    display: 'flex',
  },
  maincontent: {
    padding: theme.spacing(2),
    flexGrow: 1,
    overflow: 'hidden',
    display: 'flex',
  },
}));

interface ElementView {
  type: 'json' | 'file';
  data: string;
}

interface PropTypes {
  study: string;
}

const StudyView = (props: PropTypes) => {
  const { study } = props;
  const classes = useStyles();
  const { enqueueSnackbar } = useSnackbar();
  const [studyData, setStudyData] = useState<any>();
  const [loaded, setLoaded] = useState(false);
  const [elementView, setElementView] = useState<ElementView>();

  const initStudyData = useCallback(async (sid: string) => {
    setLoaded(false);
    try {
      const data = await getStudyData(sid, '', -1);
      setStudyData(data);
    } catch (e) {
      enqueueSnackbar(<Translation>{(t) => t('studymanager:failtoretrievedata')}</Translation>, { variant: 'error' });
      logError('Failed to fetch study data', sid, e);
    } finally {
      setLoaded(true);
    }
  }, [enqueueSnackbar]);

  useEffect(() => {
    initStudyData(study);
  }, [study, initStudyData]);


  return (
    <div className={classes.root}>
      {
        studyData && (
          <>
            <div className={classes.sidebar}>
              <div className={classes.sidebarcontent}>
                {studyData && <StudyTreeView data={studyData} view={(type, data) => setElementView({ type, data })} />}
              </div>
            </div>
            <div className={classes.main}>
              <div className={classes.maincontent}>
                {elementView && <StudyDataView type={elementView.type} data={elementView.data} />}
              </div>
            </div>
          </>
        )
      }
      {
        !loaded && <MainContentLoader />
      }
    </div>
  );
};

export default StudyView;
