import debug from 'debug';
import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Breadcrumbs, makeStyles, createStyles, Theme } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import StudyView from '../../../components/StudyView';
import { getStudyData, getStudyJobs, LaunchJob } from '../../../services/api/study';
import PulsingDot from '../../../components/ui/PulsingDot';
import GenericTabView from '../../../components/ui/NavComponents/GenericTabView'
import Informations from './Informations'

const logError = debug('antares:singlestudyview:error');

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    height: '100%',
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    flexDirection: 'column',
    overflow: 'hidden',
    boxSizing: 'border-box'
  },
  breadcrumbs: {
    backgroundColor: '#d7d7d7',
    width: '100%',
    padding: theme.spacing(1),
  },
  dot: {
    height: '0.5em',
    width: '0.5em',
  },
}));

const SingleStudyView = () => {
  const { studyId } = useParams();
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
      setStudyJobs(data);
    } catch (e) {
      logError('Failed to fetch study data', sid, e);
    }
  };

  const renderStatus = () => {
    if (studyJobs && !!studyJobs.find((j) => j.status === 'JobStatus.RUNNING')) {
      return (
        <PulsingDot style={{ height: '0.5em',
          width: '0.5em',
          marginRight: '0.5em' }}
        />
      );
    }
    return undefined;
  };

  useEffect(() => {
    if (studyId) {
      initStudyData(studyId);
      fetchStudyJob(studyId);
    }
  }, [studyId]);

  const navData = {
    'singlestudy:informations': () => <Informations studyId={studyId}/>,
    'singlestudy:treeView': () => <StudyView study={studyId} />
  }
  return (
    <div className={classes.root}>
      <Breadcrumbs aria-label="breadcrumb" className={classes.breadcrumbs}>
        <Link to="/">
          {t('main:allStudies')}
        </Link>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {renderStatus()}
          {studyname}
        </div>
      </Breadcrumbs>
      { studyId &&
        <GenericTabView items={navData}
          initialValue={'singlestudy:informations'} /> 
      }
    </div>
  );
};

export default SingleStudyView;