import React, { useState } from 'react';
import moment from 'moment';
import { makeStyles, Button, createStyles, Theme, Card, CardContent, Typography, Grid, CardActions } from '@material-ui/core';
import { useTheme } from '@material-ui/core/styles';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { StudyMetadata } from '../../common/types';
import { getExportUrl } from '../../services/api/study';
import DownloadLink from '../ui/DownloadLink';
import ConfirmationModal from '../ui/ConfirmationModal';

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

interface PropTypes {
  study: StudyMetadata;
  launchStudy: (study: StudyMetadata) => void;
  deleteStudy: (study: StudyMetadata) => void;
}

const StudyBlockSummaryView = (props: PropTypes) => {
  const classes = useStyles();
  const theme = useTheme();
  const [t] = useTranslation();
  const { study, launchStudy, deleteStudy } = props;
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);

  const deleteStudyAndCloseModal = () => {
    deleteStudy(study);
    setOpenConfirmationModal(false);
  };

  return (
    <div>
      <Card className={classes.root}>
        <CardContent>
          <Link className={classes.title} to={`/study/${encodeURI(study.id)}`}>
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
            <Button size="small" style={{ color: theme.palette.secondary.main }} onClick={() => launchStudy(study)}>{t('main:launch')}</Button>
            <DownloadLink url={getExportUrl(study.id, false)}><Button size="small" style={{ color: theme.palette.primary.light }}>{t('main:export')}</Button></DownloadLink>
            <Button size="small" style={{ float: 'right', color: theme.palette.error.main }} onClick={() => setOpenConfirmationModal(true)}>{t('main:delete')}</Button>
          </div>
        </CardActions>
        {openConfirmationModal && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={t('studymanager:confirmdelete')}
          handleYes={deleteStudyAndCloseModal}
          handleNo={() => setOpenConfirmationModal(false)}
        />
        )}
      </Card>
    </div>
  );
};

export default StudyBlockSummaryView;
