import debug from 'debug';
import React, { useCallback, useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Breadcrumbs, makeStyles, createStyles, Theme } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import { connect, ConnectedProps } from 'react-redux';
import StudyView from '../../components/StudyView';
import { getStudyData, getStudyJobs, mapLaunchJobDTO } from '../../services/api/study';
import PulsingDot from '../../components/ui/PulsingDot';
import GenericTabView from '../../components/ui/NavComponents/GenericTabView';
import Informations from '../../components/SingleStudy/Informations';
import { LaunchJob, WSMessage } from '../../common/types';
import { addListener, removeListener } from '../../ducks/websockets';

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

const SingleStudyView = (props: PropTypes) => {
  const { studyId } = useParams();
  const { addWsListener, removeWsListener } = props;
  const classes = useStyles();
  const [t] = useTranslation();
  const [studyname, setStudyname] = useState<string>();
  const [studyJobs, setStudyJobs] = useState<LaunchJob[]>();

  const initStudyData = async (sid: string) => {
    try {
      const data = await getStudyData(sid, 'study/antares', 1);
      setStudyname(data.caption as string);
    } catch (e) {
      logError('Failed to fetch study data', sid, e);
    }
  };

  const fetchStudyJob = async (sid: string) => {
    try {
      const data = await getStudyJobs(sid);
      setStudyJobs(data.reverse());
    } catch (e) {
      logError('Failed to fetch study data', sid, e);
    }
  };

  const renderStatus = () => {
    if (studyJobs && studyJobs.length > 0 && studyJobs[0].status === 'JobStatus.RUNNING') {
      return <PulsingDot style={{ height: '0.5em', width: '0.5em', marginRight: '0.5em' }} />;
    }
    return undefined;
  };

  const handleEvents = useCallback(
    (msg: WSMessage): void => {
      if (msg.type === 'STUDY_JOB_STARTED') {
        const newJob = mapLaunchJobDTO(msg.payload);
        if (newJob.studyId === studyId) {
          const existingJobs = studyJobs || [];
          setStudyJobs([newJob].concat(existingJobs));
        }
      } else if (msg.type === 'STUDY_JOB_STATUS_UPDATE' || msg.type === 'STUDY_JOB_COMPLETED') {
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
      } else if (msg.type === 'STUDY_JOB_LOG_UPDATE') {
        console.log(msg.payload);
      }
    },
    [studyJobs, studyId],
  );

  useEffect(() => {
    if (studyId) {
      initStudyData(studyId);
      fetchStudyJob(studyId);
    }
  }, [studyId]);

  useEffect(() => {
    addWsListener(handleEvents);
    return () => removeWsListener(handleEvents);
  }, [addWsListener, removeWsListener, handleEvents]);

  const navData = {
    'singlestudy:informations': () => <Informations studyId={studyId} jobs={studyJobs || []} />,
    'singlestudy:treeView': () => <StudyView study={studyId} />,
  };
  return (
    <div className={classes.root}>
      <Breadcrumbs aria-label="breadcrumb" className={classes.breadcrumbs}>
        <Link to="/" className={classes.breadcrumbsfirstelement}>
          {t('main:allStudies')}
        </Link>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {renderStatus()}
          {studyname}
        </div>
      </Breadcrumbs>
      {studyId && <GenericTabView items={navData} initialValue="singlestudy:informations" />}
    </div>
  );
};

export default connector(SingleStudyView);
