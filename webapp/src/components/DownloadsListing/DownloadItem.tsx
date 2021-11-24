import React from 'react';
import { CircularProgress, createStyles, makeStyles, Paper, Theme } from '@material-ui/core';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { useTranslation } from 'react-i18next';
import { getDownloadUrl } from '../../services/api/downloads';
import DownloadLink from '../ui/DownloadLink';
import { FileDownload } from '../../common/types';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flexGrow: 1,
    overflow: 'auto',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginLeft: theme.spacing(2),
    marginRight: theme.spacing(2),
    marginTop: theme.spacing(1),
    marginBottom: theme.spacing(1),
    padding: theme.spacing(2),
  },
  title: {
    display: 'flex',
    alignItems: 'center',
    height: theme.spacing(4),
  },
  name: {
    color: theme.palette.primary.main,
  },
  expirationInfo: {
    fontSize: '0.8em',
    fontStyle: 'italic',
    color: 'gray',
    marginLeft: theme.spacing(0.5),
  },
  actions: {
    display: 'flex',
    alignItems: 'center',
    height: theme.spacing(4),
    marginRight: theme.spacing(2),
  },
  download: {
    color: theme.palette.primary.main,
  },
}));

interface PropTypes {
  download: FileDownload;
}

export default (props: PropTypes) => {
  const { download } = props;
  const [t] = useTranslation();
  const classes = useStyles();

  return (
    <Paper className={classes.root}>
      <div className={classes.title}>
        <div className={classes.name}>
          {download.name}
        </div>
        <div className={classes.expirationInfo}>
          {`(${t('main:expirationDate')} : ${download.expirationDate})`}
        </div>
      </div>
      <div className={classes.actions}>
        <div className={classes.download}>
          {download.ready ? (
            <DownloadLink url={getDownloadUrl(download.id)}>
              <FontAwesomeIcon icon="download" />
            </DownloadLink>
          ) : <CircularProgress color="primary" style={{ width: '18px', height: '18px' }} />}
        </div>
      </div>

    </Paper>
  );
};
