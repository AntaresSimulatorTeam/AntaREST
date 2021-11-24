import React from 'react';
import clsx from 'clsx';
import { AxiosError } from 'axios';
import moment from 'moment';
import { makeStyles, Button, createStyles, Theme, Paper, Typography, Tooltip } from '@material-ui/core';
import { useTheme } from '@material-ui/core/styles';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import { getExportUrl } from '../../../services/api/study';
import { getStudyExtendedName } from '../../../services/utils';
import DownloadLink from '../../ui/DownloadLink';
import { StudyListingItemPropTypes } from './types';
import { CopyIcon } from '../../Data/utils';
import ButtonLoader from '../../ui/ButtonLoader';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';

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
    datetime: {
      color: 'gray',
      fontSize: '0.7em',
      marginLeft: theme.spacing(1.5),
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
    idInfo: {
      display: 'flex',
      fontFamily: "'Courier', sans-serif",
      fontSize: 'small',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
    },
  }));

const StudyListSummaryView = (props: StudyListingItemPropTypes) => {
  const classes = useStyles();
  const theme = useTheme();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const {
    study,
    launchStudy,
    openDeletionModal,
    importStudy,
    archiveStudy,
    unarchiveStudy,
  } = props;

  const copyId = (studyId: string): void => {
    try {
      navigator.clipboard.writeText(studyId);
      enqueueSnackbar(t('singlestudy:onStudyIdCopySuccess'), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:onStudyIdCopyError'), e as AxiosError);
    }
  };

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
          <div className={classes.workspace}>
            <div className={clsx(classes.workspaceBadge, study.managed ? classes.managed : {})}>
              {study.workspace}
            </div>
          </div>
          <Typography className={classes.datetime}>{moment.unix(study.modificationDate).format('YYYY/MM/DD HH:mm')}</Typography>
        </div>
        <div className={classes.idInfo}>
          <Typography color="textSecondary" className={classes.idInfo}>
            {study.id}
          </Typography>
          <Tooltip title={t('singlestudy:copyId') as string} placement="top">
            <CopyIcon style={{ marginLeft: '0.5em', cursor: 'pointer', color: 'grey' }} onClick={() => copyId(study.id)} />
          </Tooltip>
        </div>
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
              {t('studymanager:importcopy')}
            </ButtonLoader>
            <DownloadLink url={getExportUrl(study.id, false)}>
              <Button size="small" style={{ color: theme.palette.primary.main }}>
                {t('main:export')}
              </Button>
            </DownloadLink>
            {study.managed && (
            <ButtonLoader
              size="small"
              style={{ color: theme.palette.primary.light }}
              onClick={() => archiveStudy(study)}
            >
              {t('studymanager:archive')}
            </ButtonLoader>
            )}
          </>
        )}
        {study.managed && (
        <Button
          size="small"
          style={{ float: 'right', color: theme.palette.error.main }}
          onClick={() => openDeletionModal()}
        >
          {t('main:delete')}
        </Button>
        )}
      </div>
    </Paper>
  );
};

export default StudyListSummaryView;
