import debug from 'debug';
import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Breadcrumbs, Typography, makeStyles, createStyles, Theme } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import StudyView from '../../../components/StudyView';
import { getStudyData } from '../../../services/api/study';

const logError = debug('antares:singlestudyview:error');

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
}));

const SingleStudyView = () => {
  const { studyId } = useParams();
  const classes = useStyles();
  const [t] = useTranslation();
  const [studyname, setStudyname] = useState<string>();

  const initStudyData = async (sid: string) => {
    try {
      const data = await getStudyData(sid, 'study/antares', 1);
      setStudyname(data.caption as string);
    } catch (e) {
      logError('Failed to fetch study data', sid, e);
    }
  };

  useEffect(() => {
    if (studyId) {
      initStudyData(studyId);
    }
  }, [studyId]);

  return (
    <div className={classes.root}>
      <Breadcrumbs aria-label="breadcrumb" className={classes.breadcrumbs}>
        <Link to="/">
          {t('main:allStudies')}
        </Link>
        <Typography color="textPrimary">{studyname}</Typography>
      </Breadcrumbs>
      { studyId && <StudyView study={studyId} /> }
    </div>
  );
};

export default SingleStudyView;
