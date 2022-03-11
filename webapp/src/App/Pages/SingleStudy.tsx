import debug from 'debug';
import React, { useCallback, useEffect, useState } from 'react';
import { AxiosError } from 'axios';
import { useParams, Link, useHistory, useLocation } from 'react-router-dom';
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
import StudyViewLoader from '../../components/SingleStudy/StudyViewLoader';
import { LaunchJob, StudyMetadata, WSEvent, WSMessage } from '../../common/types';
import { addListener, removeListener } from '../../ducks/websockets';
import enqueueErrorSnackbar from '../../components/ui/ErrorSnackBar';
import MapView from '../../components/SingleStudy/MapView';
import XpansionView from '../../components/SingleStudy/XpansionView';

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
  }));

const mapState = () => ({});

const mapDispatch = {
  addWsListener: addListener,
  removeWsListener: removeListener,
};

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const useQuery = () => {
  const { search } = useLocation();

  return React.useMemo(() => new URLSearchParams(search), [search]);
};

interface MenuTab {
  [key: string]:
    () => JSX.Element;
}

const SingleStudyView = (props: PropTypes) => {
  const { studyId, tab, option } = useParams();
  const query = useQuery();
  const { addWsListener, removeWsListener } = props;
  const classes = useStyles();
  const history = useHistory();
  const [t] = useTranslation();
  const [study, setStudy] = useState<StudyMetadata>();
  const [studyJobs, setStudyJobs] = useState<LaunchJob[]>();
  const [navData, setNavData] = useState<MenuTab>({});
  const { enqueueSnackbar } = useSnackbar();

  const paramList = ['treeView', 'informations', 'variants', 'map', 'xpansion'];

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
    if (paramList.includes(tab)) {
      if (tab === 'variants') {
        if (study?.type === 'variantstudy') {
          if (query.get('create') !== 'true' && option !== 'edition') history.replace({ pathname: `/study/${studyId}/variants/edition` });
        }
      }
    } else {
      history.replace({ pathname: `/study/${studyId}/informations` });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studyId, history, tab, query]);

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

  useEffect(() => {
    const newNavData: {[key: string]: () => JSX.Element} = {
      informations: () =>
        (study ? <Informations study={study} jobs={studyJobs || []} /> : <StudyViewLoader />),
      map: () =>
        (study ? <MapView study={study} /> : <StudyViewLoader />),
      xpansion: () =>
        (study ? <XpansionView study={study} /> : <StudyViewLoader />),
    };
    if (study?.managed) {
      newNavData.variants = () => (study ? <VariantView study={study} option={option} /> : <div />);
    }
    if (!study?.archived) {
      newNavData.treeView = () => (study ? <StudyView study={study} /> : <div />);
    }
    setNavData(newNavData);
  }, [study, studyJobs, option]);

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
      <GenericTabView items={navData} studyId={studyId} initialValue={paramList.includes(tab) ? tab : 'informations'} />
    </div>
  );
};

export default connector(SingleStudyView);
