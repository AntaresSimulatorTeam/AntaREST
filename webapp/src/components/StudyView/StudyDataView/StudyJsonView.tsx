/* eslint-disable react-hooks/exhaustive-deps */
import React, { useState, useEffect } from 'react';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import ReactJson from 'react-json-view';
import { makeStyles, Theme, createStyles, Button, Paper, Typography } from '@material-ui/core';
import SaveIcon from '@material-ui/icons/Save';
import { editStudy, getStudyData } from '../../../services/api/study';
import { CommonStudyStyle } from './utils/utils';
import MainContentLoader from '../../ui/loaders/MainContentLoader';

const useStyles = makeStyles((theme: Theme) => createStyles({
  ...CommonStudyStyle(theme),
  saveButton: {
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'space-between',
    alignItems: 'center',
    height: '30px',
    marginBottom: theme.spacing(1),
  },
  buttonElement: {
    margin: theme.spacing(0.2),
  },
}));

interface PropTypes {
  data: string;
  study: string;
  refreshView: () => void;
  filterOut: Array<string>;
}

const StudyJsonView = (props: PropTypes) => {
  const { data, study, refreshView, filterOut } = props;
  const classes = useStyles();
  const { enqueueSnackbar } = useSnackbar();
  const [t] = useTranslation();
  const [jsonData, setJsonData] = useState<object>();
  const [loaded, setLoaded] = useState(false);
  const [saveAllowed, setSaveAllowed] = useState<boolean>(false);
  const [isEditable, setEditable] = useState<boolean>(true);

  const saveData = async () => {
    const tmpDataPath = data.split('/').filter((item) => item);
    const tmpPath = tmpDataPath.join('/');
    if (!loaded && jsonData) {
      try {
        await editStudy(jsonData, study, tmpPath);
        refreshView();
        enqueueSnackbar(t('studymanager:savedatasuccess'), { variant: 'success' });
        setSaveAllowed(false);
      } catch (e) {
        enqueueSnackbar(t('studymanager:failtosavedata'), { variant: 'error' });
      }
    } else {
      enqueueSnackbar(t('studymanager:failtosavedata'), { variant: 'error' });
    }
  };

  useEffect(() => {
    (async () => {
      setJsonData(undefined);
      setLoaded(false);
      const tmpDataPath = data.split('/').filter((item) => item);
      if (tmpDataPath.length > 0) {
        setEditable(!filterOut.includes(tmpDataPath[0]));
      }
      try {
        const res = await getStudyData(study, data, -1);
        setJsonData(res);
        setSaveAllowed(false);
      } catch (e) {
        enqueueSnackbar(t('studymanager:failtoretrievedata'), { variant: 'error' });
      } finally {
        setLoaded(true);
      }
    })();
  }, [data, filterOut]);

  return (
    <div className={classes.root}>
      {
        isEditable && (
        <div className={classes.header}>
          <Button
            variant="outlined"
            color="primary"
            className={classes.saveButton}
            style={{ border: '2px solid' }}
            onClick={() => saveData()}
            disabled={!saveAllowed}
          >
            <SaveIcon className={classes.buttonElement} style={{ width: '16px', height: '16px' }} />
            <Typography className={classes.buttonElement} style={{ fontSize: '12px' }}>{t('main:save')}</Typography>
          </Button>
        </div>
        )}
      <Paper className={classes.content}>
        {jsonData && <ReactJson src={jsonData} onEdit={isEditable ? (e) => { setJsonData(e.updated_src); setSaveAllowed(true); } : undefined} />}
        {!loaded && (
          <div style={{ width: '100%', height: '100%', position: 'relative' }}>
            <MainContentLoader />
          </div>
        )}
      </Paper>
    </div>
  );
};

export default StudyJsonView;
