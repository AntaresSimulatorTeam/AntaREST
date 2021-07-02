/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { makeStyles, Theme, createStyles, Paper, Typography, Button } from '@material-ui/core';
import SaveIcon from '@material-ui/icons/Save';
import { useSnackbar } from 'notistack';
import { Translation } from 'react-i18next';
import { getStudyData } from '../../../services/api/study';
import MainContentLoader from '../../ui/loaders/MainContentLoader';
import { MatrixType } from '../../../common/types';
import MatrixView from './MatrixView';

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
  button: {
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'space-between',
    alignItems: 'center',
    height: '30px',
    marginBottom: theme.spacing(1),
    marginRight: theme.spacing(1),
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
  study: string;
  url: string;
  filterOut: Array<string>;
}

const StudyMatrixView = (props: PropTypes) => {
  const { study, url, filterOut } = props;
  const classes = useStyles();
  const { enqueueSnackbar } = useSnackbar();
  const [data, setData] = useState<MatrixType>();
  const [loaded, setLoaded] = useState(false);
  const [changeStatus, setChangeStatus] = useState<boolean>(false);
  const [isEditable, setEditable] = useState<boolean>(true);

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
      enqueueSnackbar(<Translation>{(t) => t('studymanager:failtoretrievedata')}</Translation>, { variant: 'error' });
    } finally {
      setLoaded(true);
    }
  };

  const onChange = () => {
    // Save matrix if edited
    setChangeStatus(!changeStatus);
  };

  useEffect(() => {
    const urlParts = url.split('/');
    const tmpUrl = urlParts.filter((item) => item);
    if (tmpUrl.length > 0) {
      setEditable(!filterOut.includes(tmpUrl[0]));
    }
    if (urlParts.length < 2) {
      enqueueSnackbar(<Translation>{(t) => t('studymanager:failtoretrievedata')}</Translation>, { variant: 'error' });
      return;
    }
    loadFileData();
    setChangeStatus(false);
  }, [url, filterOut]);

  return (
    <>
      {data && Object.keys(data).length > 0 && (
      <div className={classes.root}>
        {
          isEditable && (
          <div className={classes.header}>
            <Button
              variant="outlined"
              color="primary"
              className={classes.button}
              style={{ border: '2px solid' }}
            >
              <Typography className={classes.buttonElement} style={{ fontSize: '12px' }}>
                <Translation>{(t) => t('main:import')}</Translation>
              </Typography>
            </Button>
            <Button
              variant="outlined"
              color="primary"
              className={classes.button}
              style={{ border: '2px solid' }}
              onClick={onChange}
            >
              {changeStatus && <SaveIcon className={classes.buttonElement} style={{ width: '16px', height: '16px' }} />}
              <Typography className={classes.buttonElement} style={{ fontSize: '12px' }}>
                <Translation>{(t) => (changeStatus ? t('main:save') : t('main:edit'))}</Translation>
              </Typography>
            </Button>
          </div>
          )}
        <Paper className={classes.content}>
          <MatrixView matrix={data} readOnly={!changeStatus} />
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

export default StudyMatrixView;
