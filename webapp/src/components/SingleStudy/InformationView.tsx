import debug from 'debug';
import moment from 'moment';
import clsx from 'clsx';
import React, { useEffect, useState } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { makeStyles, createStyles, Theme, Paper, Typography, Button, Chip, useTheme } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { useHistory } from 'react-router';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { AppState } from '../../App/reducers';
import { GroupDTO, RoleType, StudyMetadata, StudyMetadataOwner, StudyPublicMode } from '../../common/types';
import { deleteStudy as callDeleteStudy,
  launchStudy as callLaunchStudy,
  getExportUrl,
  getStudyMetadata } from '../../services/api/study';
import { removeStudies } from '../../ducks/study';
import DownloadLink from '../ui/DownloadLink';
import ConfirmationModal from '../ui/ConfirmationModal';
import PermissionModal from './PermissionModal';

const logError = debug('antares:singlestudyview:error');

const buttonStyle = (theme: Theme, color: string) => ({
  width: '120px',
  border: `2px solid ${color}`,
  color,
  margin: theme.spacing(0.5),
  '&:hover': {
    color: 'white',
    backgroundColor: color,
  },
});
const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flex: '0 0 30%',
    minWidth: '320px',
    minHeight: '250px',
    height: '95%',
    backgroundColor: 'white',
    paddingBottom: theme.spacing(1),
    margin: theme.spacing(1),
    overflow: 'hidden',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
  },
  header: {
    width: '100%',
    flex: '0 0 40px',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    backgroundColor: theme.palette.primary.main,
    paddingLeft: theme.spacing(2),
  },
  title: {
    fontWeight: 'bold',
    color: 'white',
  },
  container: {
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'space-between',
    alignItems: 'center',
    boxSizing: 'border-box',
  },
  scrollInfoContainer: {
    flex: 1,
    padding: theme.spacing(1),
    marginBottom: theme.spacing(1),
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    boxSizing: 'border-box',
    overflowX: 'hidden',
    overflowY: 'scroll',
  },
  info: {
    width: '90%',
    marginBottom: theme.spacing(0.7),
    color: theme.palette.primary.main,
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    boxSizing: 'border-box',
  },
  mainInfo: {
    width: '90%',
    color: theme.palette.primary.main,
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
  },
  infoTitleContainer: {
    marginBottom: theme.spacing(1),
  },
  infoTitle: {
    marginRight: theme.spacing(2),
    textDecoration: 'underline',
  },
  infoLabel: {
    marginRight: theme.spacing(1),
    fontWeight: 'bold',
  },
  groupList: {
    flex: 1,
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    flexWrap: 'wrap',
    '& > *': {
      margin: theme.spacing(0.5),
    },
  },
  managed: {
    backgroundColor: theme.palette.secondary.main,
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
  buttonContainer: {
    flex: '0 0 100px',
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'center',
    alignItems: 'center',
    boxSizing: 'border-box',
    padding: theme.spacing(1),
  },
  deleteContainer: {
    flex: '0 0 30px',
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-end',
    alignItems: 'flex-end',
    boxSizing: 'border-box',
  },
  launchButton: { ...buttonStyle(theme, theme.palette.primary.main), boxSizing: 'border-box' },
  exportButton: { ...buttonStyle(theme, theme.palette.primary.main), boxSizing: 'border-box' },
  deleteButton: {
    color: theme.palette.error.main,
    padding: theme.spacing(0),
    marginRight: theme.spacing(2),
    fontSize: '0.8em',
    '&:hover': {
      backgroundColor: '#0000',
    },
  },
  editIcon: {
    '&:hover': {
      color: theme.palette.secondary.main,
    },
  },
  groupLabel: {
    height: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    boxSizing: 'border-box',
  },
}));

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

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
  const { studyId, removeStudy, user } = props;
  const classes = useStyles();
  const [t] = useTranslation();
  const theme = useTheme();
  const { enqueueSnackbar } = useSnackbar();
  const history = useHistory();
  const [study, setStudy] = useState<StudyMetadata>();
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);
  const [openPermissionModal, setOpenPermissionModal] = useState<boolean>(false);

  const launchStudy = async () => {
    if (study) {
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
    if (study) {
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

  const permissionAuthorization = (): boolean => {
    if (user) {
      // User is super admin
      if (user.groups.find((elm) => elm.id === 'admin')) {
        return true;
      }

      if (study) {
        // User is owner of this study
        if (study.owner.id && study.owner.id === user.id) {
          return true;
        }
        // User is admin of 1 of study groups
        return study.groups.findIndex((studyGroupElm) => user.groups.find((userGroupElm) => studyGroupElm.id === userGroupElm.id && userGroupElm.role === RoleType.ADMIN)) >= 0;
      }
    }
    return false;
  };

  const updateInfos = (newOwner: StudyMetadataOwner, newGroups: Array<GroupDTO>, newPublicMode: StudyPublicMode) => {
    if (study) {
      const newStudy: StudyMetadata = study;
      newStudy.owner.id = newOwner.id;
      newStudy.owner.name = newOwner.name;
      newStudy.groups = newGroups;
      newStudy.publicMode = newPublicMode;
      setStudy(newStudy);
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        const studyMetadata = await getStudyMetadata(studyId);
        setStudy(studyMetadata);
      } catch (e) {
        enqueueSnackbar(t('studymanager:failtoloadstudy'), { variant: 'error' });
      }
    };
    init();
  }, [t, enqueueSnackbar, studyId]);

  return (
    study ?
      (
        <Paper className={classes.root}>
          <div className={classes.header}>
            <Typography className={classes.title}>{t('singlestudy:informations')}</Typography>
          </div>
          <div className={classes.container} style={{ height: 'calc(100% - 40px)' }}>
            <div className={classes.container} style={{ marginTop: theme.spacing(2), marginBottom: theme.spacing(3) }}>
              <div className={classes.mainInfo}>
                <Typography style={{ fontSize: '1.3em', fontWeight: 'bold' }}>{study.name}</Typography>
                <div className={classes.workspace}>
                  <div className={clsx(classes.workspaceBadge, study.managed ? classes.managed : {})}>
                    {study.workspace}
                  </div>
                </div>
              </div>
              <div className={classes.mainInfo}>
                <Typography style={{ fontSize: '0.9em', color: 'gray' }}>{study.id}</Typography>
              </div>
            </div>
            <div className={classes.scrollInfoContainer}>
              <div className={classes.container} style={{ flex: 'none', marginBottom: theme.spacing(3) }}>
                <div className={clsx(classes.info, classes.infoTitleContainer)}>
                  <Typography className={classes.infoTitle}>Informations générales</Typography>
                </div>
                <div className={classes.info}>
                  <Typography className={classes.infoLabel}>{t('singlestudy:creationDate')}</Typography>
                  <Typography variant="body2">{moment.unix(study.creationDate).format('YYYY/MM/DD HH:mm')}</Typography>
                </div>
                <div className={classes.info}>
                  <Typography className={classes.infoLabel}>{t('singlestudy:modificationDate')}</Typography>
                  <Typography variant="body2">{moment.unix(study.modificationDate).format('YYYY/MM/DD HH:mm')}</Typography>
                </div>
                <div className={classes.info}>
                  <Typography className={classes.infoLabel}>{t('singlestudy:version')}</Typography>
                  <Typography variant="body2">{study.version}</Typography>
                </div>
              </div>
              <div className={classes.container} style={{ flex: 'none' }}>
                <div className={clsx(classes.info, classes.infoTitleContainer)}>
                  <Typography className={classes.infoTitle}>{t('singlestudy:permission')}</Typography>
                  {permissionAuthorization() && <FontAwesomeIcon icon="edit" className={classes.editIcon} onClick={() => setOpenPermissionModal(true)} />}
                </div>
                <div className={classes.info}>
                  <FontAwesomeIcon className={classes.infoLabel} icon="user" />
                  <Typography>{study.owner.name}</Typography>
                </div>
                <div className={classes.info}>
                  <FontAwesomeIcon className={classes.infoLabel} icon="shield-alt" />
                  <Typography>{t(`singlestudy:${(study.publicMode as string).toLowerCase()}PublicModeText`)}</Typography>
                </div>
                {
                    study.groups.length > 0 && (
                      <div className={classes.info}>
                        <div className={classes.groupLabel}>
                          <Typography className={classes.infoLabel} style={{ fontWeight: 'normal' }}>
                            <FontAwesomeIcon className={classes.infoLabel} icon="circle" />
                            {t('singlestudy:groupsLabel')}
                          </Typography>
                        </div>
                        <div className={classes.groupList}>
                          {
                              study.groups.map((item) => <Chip key={item.id} label={item.name} color="primary" />)
                          }
                        </div>
                      </div>
                    )}
              </div>
            </div>
            <div className={classes.buttonContainer}>
              <Button
                className={classes.launchButton}
                onClick={launchStudy}
              >
                {t('main:launch')}
              </Button>
              <DownloadLink url={getExportUrl(studyId, false)}>
                <Button className={classes.exportButton}>
                  {t('main:export')}
                </Button>
              </DownloadLink>
            </div>
            <div className={classes.deleteContainer}>
              <Button
                className={classes.deleteButton}
                onClick={() => setOpenConfirmationModal(true)}
              >
                {t('main:delete')}
              </Button>
            </div>
          </div>
          {openConfirmationModal && (
          <ConfirmationModal
            open={openConfirmationModal}
            title={t('main:confirmationModalTitle')}
            message={t('studymanager:confirmdelete')}
            handleYes={deleteStudy}
            handleNo={() => setOpenConfirmationModal(false)}
          />
          )}
          {openPermissionModal && study && user && (
          <PermissionModal
            studyId={study.id}
            owner={study.owner}
            groups={study.groups}
            publicMode={study.publicMode}
            name={study.name}
            open={openPermissionModal}
            updateInfos={updateInfos}
            onClose={() => setOpenPermissionModal(false)}
          />
          )}
        </Paper>
      ) : null
  );
};

export default connector(InformationView);
