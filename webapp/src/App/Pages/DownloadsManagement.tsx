/* eslint-disable react-hooks/exhaustive-deps */
import React, { useState, useEffect } from 'react';
import debug from 'debug';
import { Translation, useTranslation } from 'react-i18next';
import { createStyles, makeStyles, Theme } from '@material-ui/core';
import { AxiosError } from 'axios';
import { useNotif } from '../../services/utils';
import MainContentLoader from '../../components/ui/loaders/MainContentLoader';
import { FileDownload, getDownloadsList } from '../../services/api/downloads';
import enqueueErrorSnackbar from '../../components/ui/ErrorSnackBar';
import DownloadsListing from '../../components/DownloadsListing';

const logError = debug('antares:studymanagement:error');

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
  },
  breadcrumbs: {
    backgroundColor: '#d7d7d7',
    padding: theme.spacing(1),
  },
  header: {
    borderBottom: '1px solid #d7d7d7',
  },
}));

const DownloadManagement = () => {
  const classes = useStyles();
  const [downloads, setDownloads] = useState<FileDownload[]>();
  const createNotif = useNotif();
  const [loaded, setLoaded] = useState(true);

  const init = async () => {
    setLoaded(false);
    try {
      const res = await getDownloadsList();
      setDownloads(res);
    } catch (e) {
      logError('woops', e);
      enqueueErrorSnackbar(createNotif, <Translation>{(t) => t('jobs:failedtoretrievedownloads')}</Translation>, e as AxiosError);
    } finally {
      setLoaded(true);
    }
  };

  useEffect(() => {
    init();
  }, []);

  return (
    <div className={classes.root}>
      {!loaded && <MainContentLoader />}
      {loaded && downloads && <DownloadsListing downloads={downloads} />}
    </div>
  );
};

export default DownloadManagement;
