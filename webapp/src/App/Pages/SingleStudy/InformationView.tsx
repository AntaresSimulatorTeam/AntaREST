import debug from 'debug';
import moment from 'moment';
import React, { useEffect, useState } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { makeStyles, createStyles, Theme, Paper, Typography, Button, GridList, GridListTile } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import {useHistory} from 'react-router'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {StudyMetadata} from '../../../common/types';
import { deleteStudy as callDeleteStudy,
         launchStudy as callLaunchStudy,
         getExportUrl,
         getStudyMetadata } from '../../../services/api/study';
import { removeStudies } from '../../../ducks/study';
import DownloadLink from '../../../components/ui/DownloadLink';
import ConfirmationModal from '../../../components/ui/ConfirmationModal';

const logError = debug('antares:singlestudyview:error');

const buttonStyle = (color: string) => {
  return {
    width: '120px',
    border: `2px solid ${color}`,
    color,
    "&:hover": {
      color: 'white',
      border: 'none',
      backgroundColor: color
    }
  }
}
const useStyles = makeStyles((theme: Theme) => createStyles({
  root:{
      flex: '0 0 30%',
      minWidth: '320px',
      minHeight: '250px',
      height: '95%',
      backgroundColor: 'white',
      paddingBottom: theme.spacing(1),
      margin: theme.spacing(1),
      border: `1px solid ${theme.palette.primary.main}`,
      overflow: 'hidden',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'space-evenly',
      alignItems: 'center',
  },
  header: {
      width: '100%',
      height: '40px',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: theme.palette.primary.main,
      paddingLeft: theme.spacing(2)     
  },
  title: {
      fontWeight: 'bold',
      color: 'white'
  },
  buttonContainer:{
    flex: 1,
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing(0.5)   
  },
  gridList:{
      width: '100%',
  },
  gridTile: {
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'center',
    alignItems: 'center',    
  },
  launchButton: buttonStyle(theme.palette.primary.main),
  exportButton: buttonStyle(theme.palette.secondary.main),
  archiveButton: buttonStyle(theme.palette.primary.light),
  deleteButton: buttonStyle(theme.palette.error.main),
  infoContainer:{
    flex: '0 0 50%',
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: theme.spacing(2) 
  },
  info: {
    width: '80%',
    margin: theme.spacing(1),
    color: theme.palette.primary.main
  },
  infotxt: {
    marginLeft: theme.spacing(1),
  }
}));

const mapState = () => ({ /* noop */ });

const mapDispatch = ({
  removeStudy: (sid: string) => removeStudies([sid]),
});

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
interface OwnProps {
  studyId: string;
}
type PropTypes = PropsFromRedux & OwnProps;

const InformationView = (props: PropTypes) => {
  const { studyId, removeStudy } = props;
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const history = useHistory();
  const [study, setStudy] = useState<StudyMetadata>();
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);

  const launchStudy = async () => {
    if(!!study)
    {
      try {
        await callLaunchStudy(study.id);
        enqueueSnackbar(t('studymanager:studylaunched', { studyname: study.name }), { variant: 'success' });
      } catch (e) {
        enqueueSnackbar(t('studymanager:failtorunstudy'), { variant: 'error' });
        logError('Failed to launch study', study, e);
      }
    }
  };

  const deleteStudy = async () => {
    if(!!study)
    {
      // eslint-disable-next-line no-alert
      try {
        await callDeleteStudy(study.id);
        removeStudy(study.id);
        history.push('/');
      } catch (e) {
        enqueueSnackbar(t('studymanager:failtodeletestudy'), { variant: 'error' });
        logError('Failed to delete study', study, e);
      }
      setOpenConfirmationModal(false);
    }
  };

  useEffect(() => {
    const init = async () => {
        try{
          const _study = await getStudyMetadata(studyId);
          setStudy(_study);
        }
        catch(e)
        {
          enqueueSnackbar(t('studymanager:failtoloadstudy'), { variant: 'error' });
        }
    }
    init();
  }, [t, enqueueSnackbar, studyId]);

  return (
        !!study ?
        (<Paper className={classes.root}>
            <div className={classes.header}>
                <Typography className={classes.title}>{t('singlestudy:informations')}</Typography>
            </div>
            <div className={classes.infoContainer}>
              <div className={classes.info}>
                <FontAwesomeIcon icon="user" />
                <span className={classes.infotxt}>{study.author}</span>
            </div>
            <div className={classes.info}>
              <FontAwesomeIcon icon="clock" />
              <span className={classes.infotxt}>{moment.unix(study.creationDate).format('YYYY/MM/DD HH:mm')}</span>
            </div>
            <div className={classes.info}>
              <FontAwesomeIcon icon="code-branch" />
              <span className={classes.infotxt}>{study.version}</span>
            </div>
            <div className={classes.info}>
              <FontAwesomeIcon icon="history" />
              <span className={classes.infotxt}>{moment.unix(study.modificationDate).format('YYYY/MM/DD HH:mm')}</span>
            </div>
            </div>
            <div className={classes.buttonContainer}>
                <GridList cellHeight={50} className={classes.gridList}>
                    <GridListTile className={classes.gridTile}>
                        <Button className={classes.launchButton}
                                onClick={launchStudy}>
                                {t('main:launch')}
                        </Button>
                    </GridListTile>
                    <GridListTile className={classes.gridTile}>
                      <DownloadLink url={getExportUrl(studyId, true, false)}>
                        <Button className={classes.exportButton}>
                                {t('main:export')}
                        </Button>
                      </DownloadLink>
                    </GridListTile>
                    <GridListTile className={classes.gridTile}>
                      <DownloadLink url={getExportUrl(studyId, false, false)}>
                        <Button className={classes.archiveButton}>
                                {t('main:archive')}
                        </Button>
                      </DownloadLink>
                    </GridListTile>
                    <GridListTile className={classes.gridTile}>
                        <Button className={classes.deleteButton}
                                onClick={() => setOpenConfirmationModal(true)}>
                                {t('main:delete')}
                        </Button>
                    </GridListTile>
                </GridList>
            </div>
            {openConfirmationModal && <ConfirmationModal open={openConfirmationModal}
                                                     title={t('main:confirmationModalTitle')}
                                                     message={t('studymanager:confirmdelete')}
                                                     handleYes={deleteStudy}
                                                     handleNo={() => setOpenConfirmationModal(false)}/>}
        </Paper>): null
  );
};

export default connector(InformationView);