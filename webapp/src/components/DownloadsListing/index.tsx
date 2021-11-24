import React from 'react';
import { makeStyles, createStyles, Theme } from '@material-ui/core';
import moment from 'moment';
import DownloadItem from './DownloadItem';
import { FileDownload } from '../../common/types';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flexGrow: 1,
    overflow: 'auto',
  },
  container: {
    display: 'flex',
    width: '100%',
    flexDirection: 'column',
    flexWrap: 'nowrap',
    paddingTop: theme.spacing(2),
    justifyContent: 'space-around',
  },
  job: {
    marginLeft: theme.spacing(3),
    marginRight: theme.spacing(3),
    marginBottom: theme.spacing(1),
    width: '100%',
  },
}));

interface PropTypes {
  downloads: FileDownload[];
}

const DownloadsListing = (props: PropTypes) => {
  const { downloads } = props;
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <div className={classes.container}>
        {
          downloads
            .sort((a, b) => (moment(a.expirationDate).isAfter(moment(b.expirationDate)) ? -1 : 1))
            .map((download) => (
              <DownloadItem download={download} />
            ))}
      </div>
    </div>
  );
};

export default DownloadsListing;
