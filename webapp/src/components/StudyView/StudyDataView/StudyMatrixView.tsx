/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { Theme, createStyles, makeStyles } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { Translation } from 'react-i18next';
import { getFileData } from '../../../services/api/file';
import MainContentLoader from '../../ui/loaders/MainContentLoader';
import {MatrixType} from "../../../common/types";

const useStyles = makeStyles((theme: Theme) => createStyles({
  code: {
    whiteSpace: 'pre',
  },
}));

interface PropTypes {
  study: string;
  url: string;
}

const StudyMatrixView = (props: PropTypes) => {
  const { study, url } = props;
  const classes = useStyles();
  const { enqueueSnackbar } = useSnackbar();
  const [data, setData] = useState<MatrixType>();
  const [loaded, setLoaded] = useState(false);

  const loadFileData = async (fileUrl: string) => {
    setData(undefined);
    setLoaded(false);
    try {
      const res = {
          columns: ["a", "b"],
          data: [[1, 2], [3, 4]],
          index: [1, 2]
      }
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
    loadFileData(`studies/${study}/${urlParts.slice(2).join('/')}`);
  }, [url]);

  return (
    <>
      {data && <code className={classes.code}>{url}</code>}
      {!loaded && (
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
          <MainContentLoader />
        </div>
      )}
    </>
  );
};

export default StudyMatrixView;