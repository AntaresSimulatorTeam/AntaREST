/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import axios, { AxiosError } from 'axios';
import { makeStyles, Theme, createStyles, Paper } from '@material-ui/core';
import debug from 'debug';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { getStudyData, importFile } from '../../../services/api/study';
import MainContentLoader from '../../ui/loaders/MainContentLoader';
import { MatrixType } from '../../../common/types';
import MatrixView from '../../ui/MatrixView/index';
import ImportForm from '../../ui/ImportForm';
import { CommonStudyStyle } from './utils/utils';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';
import NoContent from '../../ui/NoContent';
import SimpleLoader from '../../ui/loaders/SimpleLoader';

const logErr = debug('antares:createimportform:error');

const useStyles = makeStyles((theme: Theme) => createStyles({
  ...CommonStudyStyle(theme),
  button: {
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'space-between',
    alignItems: 'center',
    height: '30px',
    marginBottom: theme.spacing(1),
    marginRight: theme.spacing(1),
  },
  buttonElement: {
    margin: theme.spacing(0.2),
  },

}));

interface PropTypes {
  study: string;
  url: string;
  refreshView: () => void;
  filterOut: Array<string>;
}

const StudyMatrixView = (props: PropTypes) => {
  const { study, url, filterOut, refreshView } = props;
  const classes = useStyles();
  const { enqueueSnackbar } = useSnackbar();
  const [t] = useTranslation();
  const [data, setData] = useState<MatrixType>();
  const [loaded, setLoaded] = useState(false);
  const [isEditable, setEditable] = useState<boolean>(true);
  const [formatedPath, setFormatedPath] = useState<string>('');

  const loadFileData = async () => {
    setData(undefined);
    setLoaded(false);
    try {
      const res = await getStudyData(study, url);
      if (typeof res === 'string') {
        const fixed = res.replace(/NaN/g, '"NaN"');
        setData(JSON.parse(fixed));
      } else {
        setData(res);
      }
    } catch (e) {
      if (axios.isAxiosError(e)) {
        enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtoretrievedata'), e as AxiosError);
      } else {
        enqueueSnackbar(t('studymanager:failtoretrievedata'), { variant: 'error' });
      }
    } finally {
      setLoaded(true);
    }
  };

  const onImport = async (file: File) => {
    try {
      await importFile(file, study, formatedPath);
    } catch (e) {
      logErr('Failed to import file', file, e);
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtosavedata'), e as AxiosError);
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
      <div className={classes.root}>
        {
          isEditable && (
          <div className={classes.header}>
            <ImportForm text={t('main:import')} onImport={onImport} />
          </div>
          )}
        <Paper className={classes.content}>
          {!loaded && (
            <SimpleLoader />
          )}
          {loaded && data && Object.keys(data).length > 0 ? (
            <MatrixView matrix={data} readOnly />
          ) : (
            loaded && (
            <NoContent
              title="data:matrixEmpty"
              callToAction={
                <ImportForm text={t('main:import')} onImport={onImport} />
              }
            />
            )
          )}
        </Paper>
      </div>
      {!loaded && (
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
          <MainContentLoader />
        </div>
      )}
    </>
  );
};

export default StudyMatrixView;
