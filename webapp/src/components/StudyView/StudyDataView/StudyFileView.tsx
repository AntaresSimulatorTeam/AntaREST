/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { makeStyles, Theme, createStyles, Paper } from '@material-ui/core';
import debug from 'debug';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import MainContentLoader from '../../ui/loaders/MainContentLoader';
import { getStudyData, importFile } from '../../../services/api/study';
import ImportForm from '../../ui/ImportForm';
import { CommonStudyStyle } from './utils/utils';

const logErr = debug('antares:createimportform:error');

const useStyles = makeStyles((theme: Theme) => createStyles({
  ...CommonStudyStyle(theme),
  code: {
    whiteSpace: 'pre',
  },
}));

interface PropTypes {
  study: string;
  url: string;
  refreshView: () => void;
  filterOut: Array<string>;
}

const StudyDataView = (props: PropTypes) => {
  const { study, url, filterOut, refreshView } = props;
  const classes = useStyles();
  const { enqueueSnackbar } = useSnackbar();
  const [t] = useTranslation();
  const [data, setData] = useState<string>();
  const [loaded, setLoaded] = useState(false);
  const [isEditable, setEditable] = useState<boolean>(true);
  const [formatedPath, setFormatedPath] = useState<string>('');

  const loadFileData = async () => {
    setData(undefined);
    setLoaded(false);
    try {
      const res = await getStudyData(study, url);
      setData(res);
    } catch (e) {
      enqueueSnackbar(t('studymanager:failtoretrievedata'), { variant: 'error' });
    } finally {
      setLoaded(true);
    }
  };

  const onImport = async (file: File) => {
    try {
      await importFile(file, study, formatedPath);
    } catch (e) {
      logErr('Failed to import file', file, e);
      enqueueSnackbar(t('studymanager:failtosavedata'), { variant: 'error' });
    }
    refreshView();
    enqueueSnackbar(t('studymanager:savedatasuccess'), { variant: 'success' });
  };

  useEffect(() => {
    const urlParts = url.split('/');
    const tmpUrl = urlParts.filter((item) => item);
    setFormatedPath(tmpUrl.join('/'));
    if (tmpUrl.length > 0) {
      setEditable(!filterOut.includes(tmpUrl[0]));
    }
    if (urlParts.length < 2) {
      enqueueSnackbar(t('studymanager:failtoretrievedata'), { variant: 'error' });
      return;
    }
    loadFileData();
  }, [url, filterOut]);

  return (
    <>
      {data && (
      <div className={classes.root}>
        {
           isEditable && (
           <div className={classes.header}>
             <ImportForm text={t('main:import')} onImport={onImport} />
           </div>
           )}
        <Paper className={classes.content}>
          <code className={classes.code}>{data}</code>
        </Paper>
      </div>
      )}
      {!loaded && (
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
          <MainContentLoader />
        </div>
      )}
    </>
  );
};

export default StudyDataView;
