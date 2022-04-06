import React, { useCallback, useEffect, useState } from 'react';
import { AxiosError } from 'axios';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { createStyles, makeStyles, Theme, Box, Button } from '@material-ui/core';
import XpansionPropsView from './XpansionPropsView';
import { MatrixType, StudyMetadata } from '../../../common/types';
import SplitLayoutView from '../../ui/SplitLayoutView';
import CreateCandidateModal from './CreateCandidateModal';
import { XpansionCandidate, XpansionSettings, XpansionRenderView } from './types';
import { getAllCandidates, getXpansionSettings, xpansionConfigurationExist, getAllConstraints, getAllCapacities, createXpansionConfiguration, deleteXpansionConfiguration, addCandidate, deleteCandidate, deleteConstraints, deleteCapacity, getConstraint, getCapacity, addCapacity, addConstraints, updateCandidate, updateXpansionSettings } from '../../../services/api/xpansion';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';
import { getAllLinks } from '../../../services/api/studydata';
import { LinkCreationInfo } from '../MapView/types';
import SimpleLoader from '../../ui/loaders/SimpleLoader';
import MatrixView from '../../ui/MatrixView';
import { transformNameToId } from '../../../services/utils';
import CandidateForm from './CandidateForm';
import SettingsForm from './SettingsForm';
import XpansionTable from './XpansionTable';
import GenericModal from '../../ui/GenericModal';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    create: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      width: '100%',
      flexGrow: 1,
    },
    createButton: {
      width: '140px',
      border: `2px solid ${theme.palette.primary.main}`,
      '&:hover': {
        border: `2px solid ${theme.palette.secondary.main}`,
        color: theme.palette.secondary.main,
      },
      fontWeight: 'bold',
    },
    content: {
      padding: theme.spacing(1),
      width: '900px',
      height: '600px',
      display: 'flex',
      flexFlow: 'column nowrap',
      alignItems: 'flex-start',
      overflow: 'auto',
    },
    contentView: {
      width: '100%',
      height: '100%',
      padding: theme.spacing(2),
      boxSizing: 'border-box',
    },
  }));

interface Props {
    study: StudyMetadata;
}

const XpansionView = (props: Props) => {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const classes = useStyles();
  const { study } = props;
  const [candidateCreationModal, setCandidateCreationModal] = useState<boolean>(false);
  const [selectedItem, setSelectedItem] = useState<string>();
  const [view, setView] = useState<XpansionRenderView | undefined>();
  const [settings, setSettings] = useState<XpansionSettings>();
  const [candidates, setCandidates] = useState<Array<XpansionCandidate>>();
  const [constraints, setConstraints] = useState<Array<string>>();
  const [links, setLinks] = useState<Array<LinkCreationInfo>>();
  const [capacities, setCapacities] = useState<Array<string>>();
  const [createConfigView, setCreateConfigView] = useState<boolean>(false);
  const [loaded, setLoaded] = useState<boolean>(false);
  const [constraintViewModal, setConstraintViewModal] = useState<{filename: string; content: string}>();
  const [capacityViewModal, setCapacityViewModal] = useState<{filename: string; content: MatrixType}>();

  const initSettings = useCallback(async (after: () => void = () => { /* noop */ }) => {
    try {
      const tempSettings = await getXpansionSettings(study.id);
      setSettings(tempSettings);
      if (after) {
        after();
      }
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:xpansionError'), e as AxiosError);
    }
  }, [study.id, enqueueSnackbar, t]);

  const initCandidate = useCallback(async (after: () => void = () => { /* noop */ }) => {
    try {
      const tempCandidates = await getAllCandidates(study.id);
      for (let i = 0; i < tempCandidates.length; i += 1) {
        tempCandidates[i].link = tempCandidates.map((item) => item.link.split(' - ').map((index) => transformNameToId(index)).join(' - '))[i];
      }
      setCandidates(tempCandidates);
      if (after) {
        after();
      }
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:xpansionError'), e as AxiosError);
    }
  }, [study.id, enqueueSnackbar, t]);

  const initFiles = useCallback(async (after: () => void = () => { /* noop */ }) => {
    try {
      const tempConstraints = await getAllConstraints(study.id);
      setConstraints(tempConstraints);
      if (after) {
        after();
      }
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:xpansionError'), e as AxiosError);
    }
  }, [study.id, enqueueSnackbar, t]);

  const initCapa = useCallback(async (after: () => void = () => { /* noop */ }) => {
    try {
      const tempCapa = await getAllCapacities(study.id);
      setCapacities(tempCapa);
      if (after) {
        after();
      }
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:xpansionError'), e as AxiosError);
    }
  }, [study.id, enqueueSnackbar, t]);

  const init = useCallback(async (after: () => void = () => { /* noop */ }) => {
    try {
      const exist = await xpansionConfigurationExist(study.id);
      if (exist) {
        initSettings();
        initCandidate();
        initFiles();
        initCapa();
        const tempLinks = await getAllLinks(study.id);
        setLinks(tempLinks);
      } else {
        setCreateConfigView(true);
      }
      if (after) {
        after();
      }
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:xpansionError'), e as AxiosError);
    } finally {
      setLoaded(true);
    }
  }, [study.id, enqueueSnackbar, t, initSettings, initCandidate, initFiles, initCapa]);

  const createXpansion = async () => {
    try {
      await createXpansionConfiguration(study.id);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:createXpansionError'), e as AxiosError);
    } finally {
      setCreateConfigView(false);
      setLoaded(true);
      init();
    }
  };

  const deleteXpansion = async () => {
    try {
      await deleteXpansionConfiguration(study.id);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:deleteXpansionError'), e as AxiosError);
    } finally {
      setCreateConfigView(true);
    }
  };

  const createCandidate = async (name: string, link: string) => {
    try {
      await addCandidate(study.id, { name, link, 'annual-cost-per-mw': 1, 'max-investment': 1 });
      setCandidateCreationModal(false);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:createCandidateError'), e as AxiosError);
    } finally {
      initCandidate(() => { setSelectedItem(name); setView(XpansionRenderView.candidate); });
    }
  };

  const handleDeleteCandidate = async (name: string) => {
    if (candidates) {
      const obj = candidates.filter((o) => o.name !== name);
      try {
        await deleteCandidate(study.id, name);
        setCandidates(obj);
        setSelectedItem(undefined);
        setView(undefined);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:deleteCandidateError'), e as AxiosError);
      } finally {
        initCandidate();
      }
    }
  };

  const handleUpdateCandidate = async (name: string, value: XpansionCandidate) => {
    try {
      await updateCandidate(study.id, name, value);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:updateCandidateError'), e as AxiosError);
    } finally {
      if (name && value['annual-cost-per-mw'] && value.link) {
        initCandidate(() => setSelectedItem(name));
        enqueueSnackbar(t('studymanager:savedatasuccess'), { variant: 'success' });
      }
    }
  };

  const updateSettings = async (value: XpansionSettings) => {
    try {
      await updateXpansionSettings(study.id, value);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:updateSettingsError'), e as AxiosError);
    } finally {
      initSettings(() => setView(XpansionRenderView.settings));
      enqueueSnackbar(t('studymanager:savedatasuccess'), { variant: 'success' });
    }
  };

  const addOneConstraint = async (file: File) => {
    if (constraints) {
      try {
        await addConstraints(study.id, file);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:addFileError'), e as AxiosError);
      } finally {
        initFiles(() => setView(XpansionRenderView.files));
      }
    }
  };

  const getOneConstraint = async (filename: string) => {
    try {
      const content = await getConstraint(study.id, filename);
      setConstraintViewModal({ filename, content });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:getFileError'), e as AxiosError);
    }
  };

  const deleteConstraint = async (filename: string) => {
    if (constraints) {
      const tempConstraints = constraints.filter((a) => a !== filename);
      try {
        await deleteConstraints(study.id, filename);
        setConstraints(tempConstraints);
        setView(XpansionRenderView.files);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:deleteFileError'), e as AxiosError);
      }
    }
  };

  const addOneCapa = async (file: File) => {
    if (capacities) {
      try {
        await addCapacity(study.id, file);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:addFileError'), e as AxiosError);
      } finally {
        initCapa(() => setView(XpansionRenderView.capacities));
      }
    }
  };

  const getOneCapa = async (filename: string) => {
    try {
      const content = await getCapacity(study.id, filename);
      setCapacityViewModal({ filename, content });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:getFileError'), e as AxiosError);
    }
  };

  const deleteCapa = async (filename: string) => {
    if (capacities) {
      const tempCapa = capacities.filter((a) => a !== filename);
      try {
        await deleteCapacity(study.id, filename);
        setCapacities(tempCapa);
        setView(XpansionRenderView.capacities);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:deleteFileError'), e as AxiosError);
      }
    }
  };

  useEffect(() => {
    init();
  }, [init]);

  const onClose = () => setCandidateCreationModal(false);

  const renderView = () => {
    if (view === XpansionRenderView.candidate) {
      if (candidates) {
        const candidate = candidates.find((o) => o.name === selectedItem);
        if (candidate) {
          return (
            <CandidateForm candidate={candidate} links={links || []} capacities={capacities || []} deleteCandidate={handleDeleteCandidate} updateCandidate={handleUpdateCandidate} onRead={getOneCapa} />
          );
        }
      }
    }
    if (view === XpansionRenderView.settings) {
      if (settings) {
        return (
          <SettingsForm settings={settings} constraints={constraints || []} updateSettings={updateSettings} onRead={getOneConstraint} />
        );
      }
    }
    if (view === XpansionRenderView.files) {
      return (
        <XpansionTable title={t('main:files')} content={constraints || []} onDelete={deleteConstraint} onRead={getOneConstraint} uploadFile={addOneConstraint} />
      );
    }
    if (view === XpansionRenderView.capacities) {
      return (
        <XpansionTable title={t('xpansion:capacities')} content={capacities || []} onDelete={deleteCapa} onRead={getOneCapa} uploadFile={addOneCapa} />
      );
    }
    return (
      <></>
    );
  };

  return (
    <>
      {loaded ? createConfigView && (
        <Box className={classes.create}>
          <Button className={classes.createButton} color="primary" variant="outlined" onClick={createXpansion}>{t('xpansion:newXpansionConfig')}</Button>
        </Box>
      ) : (
        <SimpleLoader />
      )}
      {loaded && !createConfigView && (
        <SplitLayoutView
          title={t('singlestudy:xpansion')}
          left={
            <XpansionPropsView candidateList={candidates || []} onAdd={() => setCandidateCreationModal(true)} selectedItem={selectedItem || ''} setView={setView} setSelectedItem={setSelectedItem} deleteXpansion={deleteXpansion} />
          }
          right={(
            <Box className={classes.contentView}>
              {renderView()}
            </Box>
          )}
        />
      )}

      {candidateCreationModal && (
        <CreateCandidateModal
          open={candidateCreationModal}
          onClose={onClose}
          onSave={createCandidate}
          links={links || []}
        />
      )}
      {!!constraintViewModal && (
        <GenericModal
          open={!!constraintViewModal}
          title={constraintViewModal.filename}
          handleClose={() => setConstraintViewModal(undefined)}
        >
          <Box className={classes.content}>
            <code style={{ whiteSpace: 'pre' }}>{constraintViewModal.content}</code>
          </Box>
        </GenericModal>
      )}
      {!!capacityViewModal && (
        <GenericModal
          open={!!capacityViewModal}
          title={capacityViewModal.filename}
          handleClose={() => setCapacityViewModal(undefined)}
        >
          <Box className={classes.content}>
            <MatrixView
              matrix={capacityViewModal.content}
              readOnly
            />
          </Box>
        </GenericModal>
      )}
    </>
  );
};

export default XpansionView;
