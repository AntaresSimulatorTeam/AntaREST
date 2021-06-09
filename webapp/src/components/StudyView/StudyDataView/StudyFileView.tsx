/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { Theme, createStyles, makeStyles } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { Translation } from 'react-i18next';
import MainContentLoader from '../../ui/loaders/MainContentLoader';
import { getStudyData } from '../../../services/api/study';

const useStyles = makeStyles((theme: Theme) => createStyles({
  code: {
    whiteSpace: 'pre',
  },
}));

interface PropTypes {
  study: string;
  url: string;
}

const StudyDataView = (props: PropTypes) => {
  const { study, url } = props;
  const classes = useStyles();
  const { enqueueSnackbar } = useSnackbar();
  const [data, setData] = useState<string>();
  const [loaded, setLoaded] = useState(false);

  const loadFileData = async () => {
    setData(undefined);
    setLoaded(false);
    try {
      const res = await getStudyData(study, url);
      setData(res);
    } catch (e) {
      enqueueSnackbar(<Translation>{(t) => t('studymanager:failtoretrievedata')}</Translation>, { variant: 'error' });
    } finally {
      setLoaded(true);
    }
  };

  useEffect(() => {
    const urlParts = url.split('/');
    if (urlParts.length < 2) {
      enqueueSnackbar(<Translation>{(t) => t('studymanager:failtoretrievedata')}</Translation>, { variant: 'error' });
      return;
    }
    loadFileData();
  }, [url]);

  return (
    <>
      {data && <code className={classes.code}>{data}</code>}
      {!loaded && (
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
          <MainContentLoader />
        </div>
      )}
    </>
  );
};

export default StudyDataView;
