/* eslint-disable react-hooks/exhaustive-deps */
import React, { useState, useEffect } from 'react';
import debug from 'debug';
import { Translation } from 'react-i18next';
import { createStyles, makeStyles, Theme } from '@material-ui/core';
import { AxiosError } from 'axios';
import { connect, ConnectedProps } from 'react-redux';
import { useNotif } from '../../services/utils';
import MainContentLoader from '../../components/ui/loaders/MainContentLoader';
import { convertFileDownloadDTO, FileDownload, FileDownloadDTO, getDownloadsList } from '../../services/api/downloads';
import enqueueErrorSnackbar from '../../components/ui/ErrorSnackBar';
import DownloadsListing from '../../components/DownloadsListing';
import { WSEvent, WSMessage } from '../../common/types';
import { addListener, removeListener } from '../../ducks/websockets';

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

const mapState = () => ({
});

const mapDispatch = ({
  addWsListener: addListener,
  removeWsListener: removeListener,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const DownloadManagement = (props: PropTypes) => {
  const classes = useStyles();
  const { addWsListener, removeWsListener } = props;
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

  useEffect(() => {
    const listener = (ev: WSMessage) => {
      if (ev.type === WSEvent.DOWNLOAD_CREATED) {
        setDownloads((downloads || []).concat([convertFileDownloadDTO(ev.payload as FileDownloadDTO)]));
      } else if (ev.type === WSEvent.DOWNLOAD_READY) {
        setDownloads((downloads || []).map((d) => {
          const fileDownload = (ev.payload as FileDownloadDTO);
          if (d.id === fileDownload.id) {
            return convertFileDownloadDTO(fileDownload);
          }
          return d;
        }));
      } else if (ev.type === WSEvent.DOWNLOAD_READY || ev.type === WSEvent.DOWNLOAD_FAILED) {
        setDownloads((downloads || []).map((d) => {
          const fileDownload = (ev.payload as FileDownloadDTO);
          if (d.id === fileDownload.id) {
            return convertFileDownloadDTO(fileDownload);
          }
          return d;
        }));
      } else if (ev.type === WSEvent.DOWNLOAD_EXPIRED) {
        setDownloads((downloads || []).filter((d) => {
          const fileDownload = (ev.payload as FileDownloadDTO);
          return d.id !== fileDownload.id;
        }));
      }
    };
    addWsListener(listener);
    return () => removeWsListener(listener);
  }, [addWsListener, removeWsListener, downloads]);

  return (
    <div className={classes.root}>
      {!loaded && <MainContentLoader />}
      {loaded && downloads && <DownloadsListing downloads={downloads} />}
    </div>
  );
};

export default connector(DownloadManagement);
