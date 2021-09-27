import React from 'react';
import clsx from 'clsx';
import { makeStyles, Button, createStyles, Theme, Paper, Typography, Tooltip } from '@material-ui/core';
import FiberManualRecordIcon from '@material-ui/icons/FiberManualRecord';
import { useTheme } from '@material-ui/core/styles';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { getExportUrl } from '../../../services/api/study';
import { getStudyExtendedName } from '../../../services/utils';
import DownloadLink from '../../ui/DownloadLink';
import { jobStatusColors } from '../../../App/theme';
import { StudyListingItemPropTypes } from './types';
import ButtonLoader from '../../ui/ButtonLoader';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      margin: theme.spacing(1),
      paddingRight: theme.spacing(1),
      paddingLeft: theme.spacing(1),
      width: '90%',
      height: '50px',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
    },
    jobStatus: {
      width: '10px',
      height: '10px',
      marginLeft: theme.spacing(0.5),
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'flex-start',
    },
    title: {
      color: theme.palette.primary.main,
      fontWeight: 'bold',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
      textDecoration: 'none',
    },
    managed: {
      backgroundColor: theme.palette.secondary.main,
    },
    titleContainer: {
      display: 'flex',
      alignItems: 'center',
    },
    workspace: {
      marginLeft: theme.spacing(1),
    },
    workspaceBadge: {
      border: `1px solid ${theme.palette.primary.main}`,
      borderRadius: '4px',
      padding: '0 4px',
      fontSize: '0.8em',
    },
    id: {
      fontFamily: "'Courier', sans-serif",
      fontSize: 'small',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
    },
    info: {
      flex: 1,
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'center',
      alignItems: 'flex-start',
    },
    buttons: {
      flex: 1,
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-end',
      alignItems: 'center',
    },
  }));

const StudyListSummaryView = (props: StudyListingItemPropTypes) => {
  const classes = useStyles();
  const theme = useTheme();
  const [t] = useTranslation();
  const {
    study,
    launchStudy,
    openDeletionModal,
    lastJobStatus,
    importStudy,
    archiveStudy,
    unarchiveStudy,
  } = props;

  return (
    <Paper className={classes.root}>
      <div className={classes.info}>
        <div className={classes.titleContainer}>
          <Link className={classes.title} to={`/study/${encodeURI(study.id)}`}>
            <Tooltip title={getStudyExtendedName(study)}>
              <Typography className={classes.title} component="h3">
                {study.name}
              </Typography>
            </Tooltip>
          </Link>
          {!!lastJobStatus && (
            <div className={classes.jobStatus}>
              <FiberManualRecordIcon
                style={{ width: '10px', height: '10px', color: jobStatusColors[lastJobStatus] }}
              />
            </div>
          )}
          <div className={classes.workspace}>
            <div className={clsx(classes.workspaceBadge, study.managed ? classes.managed : {})}>
              {study.workspace}
            </div>
          </div>
        </div>
        <Typography color="textSecondary" className={classes.id}>
          {study.id}
        </Typography>
      </div>
      <div className={classes.buttons}>
        {study.archived ? (
          <ButtonLoader
            size="small"
            style={{ color: theme.palette.primary.light }}
            onClick={() => unarchiveStudy(study)}
          >
            {t('studymanager:unarchive')}
          </ButtonLoader>
        ) : (
          <>
            <Button
              size="small"
              style={{ color: theme.palette.secondary.main }}
              onClick={() => launchStudy(study)}
            >
              {t('main:launch')}
            </Button>
            <ButtonLoader
              size="small"
              style={{ color: theme.palette.primary.main }}
              onClick={() => importStudy(study)}
            >
              {t('main:import')}
            </ButtonLoader>
            <DownloadLink url={getExportUrl(study.id, false)}>
              <Button size="small" style={{ color: theme.palette.primary.main }}>
                {t('main:export')}
              </Button>
            </DownloadLink>
            <ButtonLoader
              size="small"
              style={{ color: theme.palette.primary.light }}
              onClick={() => archiveStudy(study)}
            >
              {t('studymanager:archive')}
            </ButtonLoader>
          </>
        )}
        <Button
          size="small"
          style={{ float: 'right', color: theme.palette.error.main }}
          onClick={() => openDeletionModal()}
        >
          {t('main:delete')}
        </Button>
      </div>
    </Paper>
  );
};

export default StudyListSummaryView;
