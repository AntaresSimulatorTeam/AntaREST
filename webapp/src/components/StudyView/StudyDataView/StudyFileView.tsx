import React, { useEffect, useState } from 'react';
import { Theme, createStyles, makeStyles } from '@material-ui/core';
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
  const [data, setData] = useState<string>();

  const loadFileData = async (fileUrl: string) => {
    const res = await getFileData(fileUrl);
    setData(res);
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
