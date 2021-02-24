import React from 'react';
import moment from 'moment';
import { useSnackbar } from 'notistack';
import { makeStyles, Button, createStyles, Theme, Card, CardContent, Typography, Grid, CardActions } from '@material-ui/core';
import { useTheme } from '@material-ui/core/styles';
import { useTranslation } from 'react-i18next';
import debug from 'debug';
import { Link } from 'react-router-dom';
import { connect, ConnectedProps } from 'react-redux';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { StudyMetadata } from '../../../common/types';
import { deleteStudy as callDeleteStudy, launchStudy as callLaunchStudy, getExportUrl } from '../../../services/api/study';
import { removeStudies } from '../../../ducks/study';
import DownloadLink from '../../ui/DownloadLink';

const logError = debug('antares:studyblockview:error');

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    margin: '10px',
    padding: '4px',
    width: '400px',
    height: '170px',
  },
  title: {
    color: theme.palette.primary.main,
    fontWeight: 'bold',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    textDecoration: 'none',
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

const mapState = () => ({ /* noop */ });

const mapDispatch = ({
  removeStudy: (sid: string) => removeStudies([sid]),
});

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
interface OwnProps {
  study: StudyMetadata;
}
type PropTypes = PropsFromRedux & OwnProps;

const StudyBlockSummaryView = (props: PropTypes) => {
  const classes = useStyles();
  const { enqueueSnackbar } = useSnackbar();
  const theme = useTheme();
  const [t] = useTranslation();
  const { study, removeStudy } = props;

  const launchStudy = async () => {
    try {
      await callLaunchStudy(study.id);
    } catch (e) {
      enqueueSnackbar(t('studymanager:failtorunstudy'), { variant: 'error' });
      logError('Failed to launch study', study, e);
    }
  };

  const deleteStudy = async () => {
    // eslint-disable-next-line no-alert
    if (window.confirm(t('studymanager:confirmdelete'))) {
      try {
        await callDeleteStudy(study.id);
        removeStudy(study.id);
      } catch (e) {
        enqueueSnackbar(t('studymanager:failtodeletestudy'), { variant: 'error' });
        logError('Failed to delete study', study, e);
      }
    }
  };

  return (
    <div>
      <Card className={classes.root}>
        <CardContent>
          <Link className={classes.title} to={`/study/${study.id}`}>
            <Typography className={classes.title} component="h3">
              {study.name}
            </Typography>
          </Link>
          <Typography color="textSecondary" className={classes.id} gutterBottom>
            {study.id}
          </Typography>
          <Grid container spacing={2} className={classes.info}>
            <Grid item xs={6}>
              <FontAwesomeIcon icon="user" />
              <span className={classes.infotxt}>{study.author}</span>
            </Grid>
            <Grid item xs={6}>
              <FontAwesomeIcon icon="clock" />
              <span className={classes.infotxt}>{moment.unix(study.creationDate).format('YYYY/MM/DD HH:mm')}</span>
            </Grid>
            <Grid item xs={6}>
              <FontAwesomeIcon icon="code-branch" />
              <span className={classes.infotxt}>{study.version}</span>
            </Grid>
            <Grid item xs={6}>
              <FontAwesomeIcon icon="history" />
              <span className={classes.infotxt}>{moment.unix(study.modificationDate).format('YYYY/MM/DD HH:mm')}</span>
            </Grid>
          </Grid>
        </CardContent>
        <CardActions>
          <div style={{ width: '100%' }}>
            <Button size="small" style={{ color: theme.palette.secondary.main }} onClick={launchStudy}>{t('main:launch')}</Button>
            <DownloadLink url={getExportUrl(study.id, true, false)}><Button size="small" style={{ color: theme.palette.primary.light }}>{t('main:export')}</Button></DownloadLink>
            <DownloadLink url={getExportUrl(study.id, false, false)}><Button size="small" style={{ color: theme.palette.primary.light }}>{t('main:archive')}</Button></DownloadLink>
            <Button size="small" style={{ float: 'right', color: theme.palette.error.main }} onClick={deleteStudy}>{t('main:delete')}</Button>
          </div>
        </CardActions>
      </Card>

    </div>
  );
};

export default connector(StudyBlockSummaryView);
