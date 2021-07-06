import React, { useState, useEffect } from 'react';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import ReactJson from 'react-json-view';
import { makeStyles, Theme, createStyles, Button, Paper, Typography } from '@material-ui/core';
import SaveIcon from '@material-ui/icons/Save';
import { editStudy } from '../../../services/api/study';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flex: 1,
    height: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
  },
  header: {
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  content: {
    padding: theme.spacing(3),
    boxSizing: 'border-box',
    flex: 1,
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    overflow: 'auto',
  },
  saveButton: {
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'space-between',
    alignItems: 'center',
    height: '30px',
    marginBottom: theme.spacing(1),
  },
  grayButton: {
    border: '2px solid gray',
    color: 'gray',
  },
  buttonElement: {
    margin: theme.spacing(0.2),
  },
}));

interface PropTypes {
  data: {path: string; json: object};
  study: string;
  studyData: any;
  setStudyData: (elm: any) => void;
  updateViewedData: (json: object) => void;
  filterOut: Array<string>;
}

const StudyJsonView = (props: PropTypes) => {
  const { data, study, studyData, setStudyData, updateViewedData, filterOut } = props;
  const classes = useStyles();
  const { enqueueSnackbar } = useSnackbar();
  const [t] = useTranslation();
  const [jsonData, setJsonData] = useState<object>(data.json);
  const [saveAllowed, setSaveAllowed] = useState<boolean>(false);
  const [isEditable, setEditable] = useState<boolean>(true);

  const writeLeaf = (keys: Array<string>, dataElm: any, value: any, index = 0) => {
    if (index >= keys.length || keys.length === 0) { return; }
    if (!(keys[index] in dataElm)) { return; }
    const key = keys[index];
    if (index === keys.length - 1) {
      // eslint-disable-next-line no-param-reassign
      dataElm[key] = value;
    } else {
      writeLeaf(keys, dataElm[key], value, index + 1);
    }
  };

  const saveData = async () => {
    const tmpDataPath = data.path.split('/').filter((item) => item);
    const tmpPath = tmpDataPath.join('/');

    try {
      await editStudy(jsonData, study, tmpPath);
      const newData = { ...studyData };
      writeLeaf(tmpDataPath, newData, jsonData);
      setStudyData(newData);
      updateViewedData(jsonData);
      enqueueSnackbar(t('studymanager:savedatasuccess'), { variant: 'success' });
      setSaveAllowed(false);
    } catch (e) {
      enqueueSnackbar(t('studymanager:failtosavedata'), { variant: 'error' });
    }
  };
  useEffect(() => {
    const tmpDataPath = data.path.split('/').filter((item) => item);
    if (tmpDataPath.length > 0) {
      setEditable(!filterOut.includes(tmpDataPath[0]));
    }
    setJsonData(data.json);
    setSaveAllowed(false);
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
        <ReactJson src={jsonData} onEdit={isEditable ? (e) => { setJsonData(e.updated_src); setSaveAllowed(true); } : undefined} />
      </Paper>
    </div>
  );
};

export default StudyJsonView;
