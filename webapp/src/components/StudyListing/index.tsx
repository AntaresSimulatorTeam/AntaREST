import React from 'react';
import debug from 'debug';
import { connect, ConnectedProps } from 'react-redux';
import { createStyles, makeStyles, Theme } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { StudyMetadata } from '../../common/types';
import { removeStudies } from '../../ducks/study';
import {
  deleteStudy as callDeleteStudy,
  launchStudy as callLaunchStudy,
  copyStudy as callCopyStudy,
  archiveStudy as callArchiveStudy,
  unarchiveStudy as callUnarchiveStudy,
} from '../../services/api/study';
import StudyListElementView from './StudyListingItemView';
import clsx from 'clsx';

const logError = debug('antares:studyblockview:error');

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      flexGrow: 1,
      overflow: 'auto',
    },
    containerGrid: {
      display: 'flex',
      width: '100%',
      flexWrap: 'wrap',
      paddingTop: theme.spacing(2),
      justifyContent: 'space-around',
    },
    containerList: {
      display: 'flex',
      width: '100%',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      paddingTop: theme.spacing(2),
    },
  }));

const mapState = () => ({
  /* noop */
});

const mapDispatch = {
  removeStudy: (sid: string) => removeStudies([sid]),
};

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
interface OwnProps {
  studies: StudyMetadata[];
  isList: boolean;
}
type PropTypes = PropsFromRedux & OwnProps;

const StudyListing = (props: PropTypes) => {
  const classes = useStyles();
  const { studies, removeStudy, isList } = props;
  const { enqueueSnackbar } = useSnackbar();
  const [t] = useTranslation();
  const launchStudy = async (study: StudyMetadata) => {
    try {
      await callLaunchStudy(study.id);
      enqueueSnackbar(t('studymanager:studylaunched', { studyname: study.name }), {
        variant: 'success',
      });
    } catch (e) {
      enqueueSnackbar(t('studymanager:failtorunstudy'), { variant: 'error' });
      logError('Failed to launch study', study, e);
    }
  };

  const importStudy = async (study: StudyMetadata, withOutputs = false) => {
    try {
      await callCopyStudy(study.id, `${study.name} (${t('main:copy')})`, withOutputs);
      enqueueSnackbar(t('studymanager:studycopiedsuccess', { studyname: study.name }), {
        variant: 'success',
      });
    } catch (e) {
      enqueueSnackbar(t('studymanager:failtocopystudy'), { variant: 'error' });
      logError('Failed to copy/import study', study, e);
    }
  };

  const archiveStudy = async (study: StudyMetadata) => {
    try {
      await callArchiveStudy(study.id);
      enqueueSnackbar(t('studymanager:archivesuccess', { studyname: study.name }), {
        variant: 'success',
      });
    } catch (e) {
      enqueueSnackbar(t('studymanager:archivesuccess', { studyname: study.name }), {
        variant: 'error',
      });
    }
  };

  const unarchiveStudy = async (study: StudyMetadata) => {
    try {
      await callUnarchiveStudy(study.id);
      enqueueSnackbar(t('studymanager:unarchivesuccess', { studyname: study.name }), {
        variant: 'success',
      });
    } catch (e) {
      enqueueSnackbar(t('studymanager:unarchivefailure', { studyname: study.name }), {
        variant: 'error',
      });
    }
  };

  const deleteStudy = async (study: StudyMetadata) => {
    // eslint-disable-next-line no-alert
    try {
      await callDeleteStudy(study.id);
      removeStudy(study.id);
    } catch (e) {
      enqueueSnackbar(t('studymanager:failtodeletestudy'), { variant: 'error' });
      logError('Failed to delete study', study, e);
    }
  };

  return (
    <div className={clsx(classes.root, 'studylistingcontainer')}>
      <div className={isList ? classes.containerList : classes.containerGrid}>
        {studies.map((s) => (
          <StudyListElementView
            key={s.id}
            study={s}
            listMode={isList}
            importStudy={importStudy}
            launchStudy={launchStudy}
            deleteStudy={deleteStudy}
            archiveStudy={archiveStudy}
            unarchiveStudy={unarchiveStudy}
          />
        ))}
      </div>
    </div>
  );
};

export default connector(StudyListing);
