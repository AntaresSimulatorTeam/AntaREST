/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { makeStyles, Theme, createStyles, Paper, Typography, Button } from '@material-ui/core';
import debug from 'debug';
import SaveIcon from '@material-ui/icons/Save';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { getStudyData, importFile } from '../../../services/api/study';
import MainContentLoader from '../../ui/loaders/MainContentLoader';
import { MatrixType } from '../../../common/types';
import MatrixView from './MatrixView';
import ImportForm from '../../ui/ImportForm';
import { CommonStudyStyle } from './utils/utils';

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
  studyData: any;
  setStudyData: (elm: any) => void;
  filterOut: Array<string>;
}

const StudyMatrixView = (props: PropTypes) => {
  const { study, url, filterOut, studyData, setStudyData } = props;
  const classes = useStyles();
  const { enqueueSnackbar } = useSnackbar();
  const [t] = useTranslation();
  const [data, setData] = useState<MatrixType>();
  const [loaded, setLoaded] = useState(false);
  const [changeStatus, setChangeStatus] = useState<boolean>(false);
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
      enqueueSnackbar(t('studymanager:failtoretrievedata'), { variant: 'error' });
    } finally {
      setLoaded(true);
    }
  };

  const onChange = () => {
    // Save matrix if edited
    setChangeStatus(!changeStatus);
  };

  const onImport = async (file: File) => {
    try {
      await importFile(file, study, formatedPath);
    } catch (e) {
      logErr('Failed to import file', file, e);
      enqueueSnackbar(t('studymanager:failtosavedata'), { variant: 'error' });
    }
    const newData = { ...studyData };
    setStudyData(newData);
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
    setChangeStatus(false);
  }, [url, filterOut]);

  return (
    <>
      <div className={classes.root}>
        {
          isEditable && (
          <div className={classes.header}>
            <ImportForm text={t('main:import')} onImport={onImport} />
            {data && Object.keys(data).length > 0 && (
              <Button
                variant="outlined"
                color="primary"
                className={classes.button}
                style={{ border: '2px solid' }}
                onClick={onChange}
              >
                {changeStatus && <SaveIcon className={classes.buttonElement} style={{ width: '16px', height: '16px' }} />}
                <Typography className={classes.buttonElement} style={{ fontSize: '12px' }}>
                  {changeStatus ? t('main:save') : t('main:edit')}
                </Typography>
              </Button>
            )}
          </div>
          )}
        <Paper className={classes.content}>
          {data && Object.keys(data).length > 0 && (
            <MatrixView matrix={data} readOnly={!changeStatus} />
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
