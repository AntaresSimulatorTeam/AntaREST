import React from 'react';
import clsx from 'clsx';
import moment from 'moment';
import {
  makeStyles,
  Button,
  createStyles,
  Theme,
  Card,
  CardContent,
  Typography,
  Grid,
  CardActions,
} from '@material-ui/core';
import FiberManualRecordIcon from '@material-ui/icons/FiberManualRecord';
import { useTheme } from '@material-ui/core/styles';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { getExportUrl } from '../../../services/api/study';
import DownloadLink from '../../ui/DownloadLink';
import { jobStatusColors } from '../../../App/theme';
import { StudyListingItemPropTypes } from './types';
import ButtonLoader from '../../ui/ButtonLoader';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      margin: '10px',
      padding: '4px',
      width: '400px',
      height: '170px',
    },
    jobStatus: {
      width: '20px',
      marginLeft: theme.spacing(1),
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'flex-end',
    },
    buttons: {
      width: '100%',
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
      marginTop: theme.spacing(1),
    },
    infotxt: {
      marginLeft: theme.spacing(1),
    },
    pos: {
      marginBottom: 12,
    },
  }));

const StudyBlockSummaryView = (props: StudyListingItemPropTypes) => {
  const classes = useStyles();
  const theme = useTheme();
  const [t] = useTranslation();
  const { study, launchStudy, openDeletionModal, lastJobStatus, archiveStudy, unarchiveStudy } =
    props;

  return (
    <Card className={classes.root}>
      <CardContent>
        <div className={classes.titleContainer}>
          <Link className={classes.title} to={`/study/${encodeURI(study.id)}`}>
            <Typography className={classes.title} component="h3">
              {study.name}
              {!!lastJobStatus && (
                <span className={classes.jobStatus}>
                  <FiberManualRecordIcon
                    style={{ width: '15px', height: '15px', color: jobStatusColors[lastJobStatus] }}
                  />
                </span>
              )}
            </Typography>
          </Link>
          <div className={classes.workspace}>
            <div className={clsx(classes.workspaceBadge, study.managed ? classes.managed : {})}>
              {study.workspace}
            </div>
          </div>
        </div>
        <Typography color="textSecondary" className={classes.id} gutterBottom>
          {study.id}
        </Typography>
        <Grid container spacing={2} className={classes.info}>
          <Grid item xs={6}>
            <FontAwesomeIcon icon="user" />
            <span className={classes.infotxt}>{study.owner.name}</span>
          </Grid>
          <Grid item xs={6}>
            <FontAwesomeIcon icon="clock" />
            <span className={classes.infotxt}>
              {moment.unix(study.creationDate).format('YYYY/MM/DD HH:mm')}
            </span>
          </Grid>
          <Grid item xs={6}>
            <FontAwesomeIcon icon="code-branch" />
            <span className={classes.infotxt}>{study.version}</span>
          </Grid>
          <Grid item xs={6}>
            <FontAwesomeIcon icon="history" />
            <span className={classes.infotxt}>
              {moment.unix(study.modificationDate).format('YYYY/MM/DD HH:mm')}
            </span>
          </Grid>
        </Grid>
      </CardContent>
      <CardActions>
        <div className={classes.buttons}>
          {study.archived ? (
            <ButtonLoader
              size="small"
              style={{ color: theme.palette.primary.light }}
              onClick={() => unarchiveStudy(study)}
            >
              {t('studymanager:archive')}
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
        </div>
        <Button
          size="small"
          style={{ float: 'right', color: theme.palette.error.main }}
          onClick={() => openDeletionModal()}
        >
          {t('main:delete')}
        </Button>
      </CardActions>
    </Card>
  );
};

StudyBlockSummaryView.defaultProps = {
  lastJobStatus: undefined,
};

export default StudyBlockSummaryView;
