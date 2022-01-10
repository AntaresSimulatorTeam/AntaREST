import React, { useState } from 'react';
import clsx from 'clsx';
import { AxiosError } from 'axios';
import { makeStyles, Button, createStyles, Theme, Paper, Typography, Tooltip, Menu, MenuItem } from '@material-ui/core';
import { useTheme } from '@material-ui/core/styles';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import { exportStudy } from '../../../services/api/study';
import { convertUTCToLocalTime, getStudyExtendedName } from '../../../services/utils';
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
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [openMenu, setOpenMenu] = useState<string>('');

  const copyId = (studyId: string): void => {
    try {
      navigator.clipboard.writeText(studyId);
      enqueueSnackbar(t('singlestudy:onStudyIdCopySuccess'), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:onStudyIdCopyError'), e as AxiosError);
    }
  };

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
    setOpenMenu(event.currentTarget.id);
  };

  const handleClose = () => {
    setAnchorEl(null);
    setOpenMenu('');
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
          <Typography className={classes.datetime}>{convertUTCToLocalTime(study.modificationDate)}</Typography>
        </div>
        {study.managed && (
          <div className={classes.idInfo}>
            <Typography color="textSecondary" className={classes.idInfo}>
              {study.id}
            </Typography>
            <Tooltip title={t('singlestudy:copyId') as string} placement="top">
              <CopyIcon style={{ marginLeft: '0.5em', cursor: 'pointer', color: 'grey' }} onClick={() => copyId(study.id)} />
            </Tooltip>
          </div>
        )}
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
            <Button
              aria-controls="import-menu"
              aria-haspopup="true"
              size="small"
              id="import"
              style={{ color: theme.palette.primary.main }}
              onClick={handleClick}
            >
              {t('studymanager:importcopy')}
            </Button>
            <Menu
              id="import-menu"
              anchorEl={anchorEl}
              keepMounted
              open={openMenu === 'import'}
              onClose={handleClose}
            >
              <MenuItem onClick={() => { importStudy(study, true); handleClose(); }}>{t('studymanager:copyWith')}</MenuItem>
              <MenuItem onClick={() => { importStudy(study, false); handleClose(); }}>{t('studymanager:copyWithout')}</MenuItem>
            </Menu>
            <Button
              aria-controls="export-menu"
              aria-haspopup="true"
              size="small"
              id="export"
              style={{ color: theme.palette.primary.main }}
              onClick={handleClick}
            >
              {t('main:export')}
            </Button>
            <Menu
              id="export-menu"
              anchorEl={anchorEl}
              keepMounted
              open={openMenu === 'export'}
              onClose={handleClose}
            >
              <MenuItem onClick={() => { exportStudy(study.id, false); handleClose(); }}>{t('studymanager:exportWith')}</MenuItem>
              <MenuItem onClick={() => { exportStudy(study.id, true); handleClose(); }}>{t('studymanager:exportWithout')}</MenuItem>
            </Menu>
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
