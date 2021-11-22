import React from 'react';
import { Paper } from '@material-ui/core';
import { FileDownload, getDownloadUrl } from '../../services/api/downloads';
import DownloadLink from '../ui/DownloadLink';

interface PropTypes {
  download: FileDownload;
}

export default (props: PropTypes) => {
  const { download } = props;

  return (
    <Paper>
      <DownloadLink url={getDownloadUrl(download.id)}><div>{download.name}</div></DownloadLink>
    </Paper>
  );
};
