import React, { useEffect, useState } from 'react';
import { Theme, createStyles, makeStyles } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { Translation } from 'react-i18next';
import { getFileData } from '../../../services/api/file';

const useStyles = makeStyles((theme: Theme) => createStyles({
  code: {
    whiteSpace: 'pre-wrap',
  },
}));

interface PropTypes {
  url: string;
}

const StudyDataView = (props: PropTypes) => {
  const { url } = props;
  const classes = useStyles();
  const { enqueueSnackbar } = useSnackbar();
  const [data, setData] = useState<string>();

  const loadFileData = async (fileUrl: string) => {
    try {
      const res = await getFileData(fileUrl);
      setData(res);
    } catch (e) {
      enqueueSnackbar(<Translation>{(t) => t('studymanager:failtoretrievedata')}</Translation>, { variant: 'error' });
    }
  };

  useEffect(() => {
    loadFileData(url);
  }, [url]);

  return (
    <div>
      {data && <code className={classes.code}>{data}</code>}
    </div>
  );
};

export default StudyDataView;
