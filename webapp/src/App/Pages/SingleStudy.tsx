import debug from 'debug';
import React, { useCallback, useEffect, useState } from 'react';
import ContentLoader from 'react-content-loader';
import { AxiosError } from 'axios';
import { useParams, Link, useHistory } from 'react-router-dom';
import { Breadcrumbs, makeStyles, createStyles, Theme } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { connect, ConnectedProps } from 'react-redux';
import StudyView from '../../components/StudyView';
import { getStudyJobs, getStudyMetadata, mapLaunchJobDTO } from '../../services/api/study';
import PulsingDot from '../../components/ui/PulsingDot';
import GenericTabView from '../../components/ui/NavComponents/GenericTabView';
import Informations from '../../components/SingleStudy/Informations';
import VariantView from '../../components/Variants/VariantView';
import { LaunchJob, StudyMetadata, WSEvent, WSMessage } from '../../common/types';
import { addListener, removeListener } from '../../ducks/websockets';
import enqueueErrorSnackbar from '../../components/ui/ErrorSnackBar';

const logError = debug('antares:singlestudyview:error');

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      height: '100%',
      width: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      flexDirection: 'column',
      overflow: 'hidden',
      boxSizing: 'border-box',
    },
    breadcrumbs: {
      backgroundColor: '#d7d7d7',
      width: '100%',
      padding: theme.spacing(1),
    },
    breadcrumbsfirstelement: {
      marginLeft: theme.spacing(1),
    },
    dot: {
      height: '0.5em',
      width: '0.5em',
    },
    contentloader: {
      width: '100%',
      height: '100%',
    },
    contentloader1: {
      width: '100%',
      height: '100%',
      zIndex: 0,
      position: 'absolute',
    },
    contentloader2: {
      width: '100%',
      height: '100%',
      zIndex: 10,
      position: 'absolute',
    },
  }));

const mapState = () => ({});

const mapDispatch = {
  addWsListener: addListener,
  removeWsListener: removeListener,
};

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const SingleStudyView = (props: PropTypes) => {
  const { studyId, tab = 'informations', option } = useParams();
  const { addWsListener, removeWsListener } = props;
  const classes = useStyles();
  const history = useHistory();
  const [t] = useTranslation();
  const [study, setStudy] = useState<StudyMetadata>();
  const [studyJobs, setStudyJobs] = useState<LaunchJob[]>();
  const [initTab, setInitTab] = useState<string>('informations');
  const { enqueueSnackbar } = useSnackbar();

  const fetchStudyInfo = useCallback(async () => {
    try {
      const studyMetadata = await getStudyMetadata(studyId);
      setStudy(studyMetadata);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtoloadstudy'), e as AxiosError);
    }
  }, [studyId, enqueueSnackbar, t]);

  const fetchStudyJob = async (sid: string) => {
    try {
      const data = await getStudyJobs(sid);
      setStudyJobs(data.reverse());
    } catch (e) {
      logError('Failed to fetch study data', sid, e);
    }
  };

  const renderStatus = () => {
    if (studyJobs && studyJobs.length > 0 && studyJobs[0].status === 'running') {
      return <PulsingDot style={{ height: '0.5em', width: '0.5em', marginRight: '0.5em' }} />;
    }
    return undefined;
  };

  const handleEvents = useCallback(
    (msg: WSMessage): void => {
      if (msg.type === WSEvent.STUDY_JOB_STARTED) {
        const newJob = mapLaunchJobDTO(msg.payload);
        if (newJob.studyId === studyId) {
          const existingJobs = studyJobs || [];
          setStudyJobs([newJob].concat(existingJobs));
        }
      } else if (
        msg.type === WSEvent.STUDY_JOB_STATUS_UPDATE ||
        msg.type === WSEvent.STUDY_JOB_COMPLETED
      ) {
        const newJob = mapLaunchJobDTO(msg.payload);
        if (newJob.studyId === studyId) {
          const existingJobs = studyJobs || [];
          if (!existingJobs.find((j) => j.id === newJob.id)) {
            setStudyJobs([newJob].concat(existingJobs));
          } else {
            setStudyJobs(
              existingJobs.map((j) => {
                if (j.id === newJob.id) {
                  return newJob;
                }
                return j;
              }),
            );
          }
        }
      } else if (msg.type === WSEvent.STUDY_JOB_LOG_UPDATE) {
        // TODO
      } else if (msg.type === WSEvent.STUDY_EDITED) {
        fetchStudyInfo();
      }
    },
    [studyId, studyJobs, fetchStudyInfo],
  );
  useEffect(() => {
    if (tab === 'informations' || tab === 'treeView') setInitTab(tab);
    else if (tab === 'variants') {
      setInitTab('variants');
      if (study?.type === 'variantstudy') {
        history.replace({ pathname: `/study/${studyId}/variants/edition` });
      } else {
        history.replace({ pathname: `/study/${studyId}/variants` });
      }
    } else {
      setInitTab('informations');
      history.replace({ pathname: `/study/${studyId}/informations` });
    }
  }, [studyId, history, tab, study]);

  useEffect(() => {
    if (studyId) {
      fetchStudyInfo();
      fetchStudyJob(studyId);
    }
  }, [studyId, t, enqueueSnackbar, fetchStudyInfo]);

  useEffect(() => {
    addWsListener(handleEvents);
    return () => removeWsListener(handleEvents);
  }, [addWsListener, removeWsListener, handleEvents]);

  const navData: { [key: string]: () => JSX.Element } = {
    informations: () =>
      (study ? <Informations study={study} jobs={studyJobs || []} /> : (
        <div className={classes.contentloader}>
          <ContentLoader
            speed={2}
            backgroundColor="#dedede"
            foregroundColor="#ececec"
            className={classes.contentloader1}
          >
            <rect x="1%" y="2%" rx="2" ry="2" width="30%" height="85%" />
            <rect x="32%" y="2%" rx="2" ry="2" width="67%" height="41%" />
            <rect x="32%" y="45%" rx="2" ry="2" width="67%" height="42%" />
          </ContentLoader>
          <ContentLoader
            speed={2}
            backgroundColor="#B9B9B9"
            foregroundColor="#ececec"
            className={classes.contentloader2}
          >
            <rect x="1%" y="2%" rx="2" ry="2" width="30%" height="4%" />
            <rect x="32%" y="2%" rx="2" ry="2" width="67%" height="4%" />
            <rect x="32%" y="45%" rx="2" ry="2" width="67%" height="4%" />

            <rect x="3%" y="9%" rx="2" ry="2" width="20%" height="3%" />
            <rect x="3%" y="13%" rx="2" ry="2" width="19%" height="2%" />

            <rect x="3%" y="18%" rx="2" ry="2" width="11%" height="3%" />
            <rect x="3%" y="22%" rx="2" ry="2" width="8%" height="2%" />
            <rect x="12%" y="22%" rx="2" ry="2" width="8%" height="2%" />
            <rect x="3%" y="25%" rx="2" ry="2" width="10%" height="2%" />
            <rect x="14%" y="25%" rx="2" ry="2" width="8%" height="2%" />
            <rect x="3%" y="28%" rx="2" ry="2" width="4%" height="2%" />
            <rect x="8%" y="28%" rx="2" ry="2" width="2%" height="2%" />

            <rect x="3%" y="34%" rx="2" ry="2" width="7%" height="3%" />
            <rect x="3%" y="38%" rx="2" ry="2" width="6%" height="2%" />
            <rect x="3%" y="41%" rx="2" ry="2" width="11%" height="2%" />

            <rect x="12%" y="52%" rx="2" ry="2" width="7%" height="6%" />
            <rect x="12%" y="59%" rx="2" ry="2" width="7%" height="6%" />

            <rect x="25%" y="83%" rx="2" ry="2" width="5%" height="2%" />
          </ContentLoader>
        </div>
      )),
  };
  if (study?.managed) {
    navData.variants = () => (study ? <VariantView study={study} option={option} /> : <div />);
  }
  if (!study?.archived) {
    navData.treeView = () => (study ? <StudyView study={study} /> : <div />);
  }

  return (
    <div className={classes.root}>
      <Breadcrumbs aria-label="breadcrumb" className={classes.breadcrumbs}>
        <Link to="/" className={classes.breadcrumbsfirstelement}>
          {t('main:allStudies')}
        </Link>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {renderStatus()}
          {study?.name || '...'}
        </div>
      </Breadcrumbs>
      <GenericTabView items={navData} studyId={studyId} initialValue={initTab} />
    </div>
  );
};

export default connector(SingleStudyView);
