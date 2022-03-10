import React, { useCallback, useEffect, useState } from 'react';
import { AxiosError } from 'axios';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { createStyles, makeStyles, Theme, Box, Button } from '@material-ui/core';
import XpansionPropsView from './XpansionPropsView';
import { MatrixType, StudyMetadata } from '../../../common/types';
import SplitLayoutView from '../../ui/SplitLayoutView';
import CreateCandidateModal from './CreateCandidateModal';
import { XpansionCandidate, XpansionSettings } from './types';
import XpansionForm from './XpansionForm';
import { getAllCandidates, getXpansionSettings, xpansionConfigurationExist, getAllConstraints, getAllCapacities, createXpansionConfiguration, deleteXpansionConfiguration, addCandidate, deleteCandidate, deleteConstraints, deleteCapacity, getConstraint, getCapacity, addCapacity, addConstraints, updateCandidate, updateXpansionSettings } from '../../../services/api/xpansion';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';
import { getAllLinks } from '../../../services/api/studydata';
import { LinkCreationInfo } from '../MapView/types';
import SimpleLoader from '../../ui/loaders/SimpleLoader';
import XpansionTableModal from './XpansionTableModal';
import MatrixView from '../../ui/MatrixView';
import { transformNameToId } from '../../../services/utils';

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
  }));

interface Props {
    study: StudyMetadata;
}

const XpansionView = (props: Props) => {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const classes = useStyles();
  const { study } = props;
  const [openModal, setOpenModal] = useState<boolean>(false);
  const [selectedItem, setSelectedItem] = useState<XpansionCandidate | XpansionSettings | Array<string>>();
  const [settings, setSettings] = useState<XpansionSettings>();
  const [candidates, setCandidates] = useState<Array<XpansionCandidate>>();
  const [constraints, setConstraints] = useState<Array<string>>();
  const [links, setLinks] = useState<Array<LinkCreationInfo>>();
  const [capacities, setCapacities] = useState<Array<string>>();
  const [createConfigView, setCreateConfigView] = useState<boolean>(false);
  const [loaded, setLoaded] = useState<boolean>(false);
  const [singleConstraint, setSingleConstraint] = useState<{filename: string; content: string}>();
  const [singleCapa, setSingleCapa] = useState<{filename: string; content: MatrixType}>();

  const init = useCallback(async (after: () => void = () => { /* noop */ }) => {
    try {
      const exist = await xpansionConfigurationExist(study.id);
      if (exist) {
        const tempSettings = await getXpansionSettings(study.id);
        setSettings(tempSettings);
        const tempCandidates = await getAllCandidates(study.id);
        for (let i = 0; i < tempCandidates.length; i += 1) {
          tempCandidates[i].link = tempCandidates.map((item) => item.link.split(' - ').map((index) => transformNameToId(index)).join(' - '))[i];
        }
        setCandidates(tempCandidates);
        const tempConstraints = await getAllConstraints(study.id);
        setConstraints(tempConstraints);
        const tempLinks = await getAllLinks(study.id);
        setLinks(tempLinks);
        const tempCapa = await getAllCapacities(study.id);
        setCapacities(tempCapa);
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
  }, [study.id, enqueueSnackbar, t]);

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
      await addCandidate(study.id, { name, link, 'annual-cost-per-mw': 0, 'max-investment': 0 });
      setOpenModal(false);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:createCandidateError'), e as AxiosError);
    } finally {
      init(() => setSelectedItem({ name, link, 'annual-cost-per-mw': 0, 'max-investment': 0 }));
    }
  };

  const handleDeleteCandidate = async (name: string) => {
    if (candidates) {
      const obj = candidates.filter((o) => o.name !== name);
      try {
        await deleteCandidate(study.id, name);
        setCandidates(obj);
        setSelectedItem(undefined);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:deleteCandidateError'), e as AxiosError);
      } finally {
        init();
      }
    }
  };

  const handleUpdateCandidate = async (name: string, value: XpansionCandidate) => {
    try {
      await updateCandidate(study.id, name, value);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:updateCandidateError'), e as AxiosError);
    } finally {
      init(() => setSelectedItem(value));
      enqueueSnackbar(t('studymanager:savedatasuccess'), { variant: 'success' });
    }
  };

  const updateSettings = async (value: XpansionSettings) => {
    try {
      await updateXpansionSettings(study.id, value);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:updateSettingsError'), e as AxiosError);
    } finally {
      init(() => setSelectedItem(value));
      enqueueSnackbar(t('studymanager:savedatasuccess'), { variant: 'success' });
    }
  };

  const addOneConstraint = async (file: File) => {
    if (constraints) {
      try {
        await addConstraints(study.id, file);
        // setConstraints([...constraints, file.name]);
        // setSelectedItem([...constraints, file.name]);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:addFileError'), e as AxiosError);
      } finally {
        init(() => setSelectedItem([...constraints, file.name].sort()));
      }
    }
  };

  const getOneConstraint = async (filename: string) => {
    try {
      const content = await getConstraint(study.id, filename);
      setSingleConstraint({ filename, content });
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
        setSelectedItem(tempConstraints);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:deleteFileError'), e as AxiosError);
      }
    }
  };

  const getOneCapa = async (filename: string) => {
    try {
      const content = await getCapacity(study.id, filename);
      setSingleCapa({ filename, content });
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
        setSelectedItem(tempCapa);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('xpansion:deleteFileError'), e as AxiosError);
      }
    }
  };

  useEffect(() => {
    init();
  }, [init]);

  const onClose = () => setOpenModal(false);

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
            <XpansionPropsView candidateList={candidates || []} settings={settings} constraints={constraints} capacities={capacities} onAdd={() => setOpenModal(true)} selectedItem={selectedItem} setSelectedItem={setSelectedItem} deleteXpansion={deleteXpansion} />
          }
          right={
            selectedItem && (
              <XpansionForm selectedItem={selectedItem} links={links || []} constraints={constraints || []} capacities={capacities || []} deleteCandidate={handleDeleteCandidate} updateCandidate={handleUpdateCandidate} updateSettings={updateSettings} deleteConstraint={deleteConstraint} deleteCapa={deleteCapa} getConstraint={getOneConstraint} getCapacity={getOneCapa} addConstraint={addOneConstraint} addCapacity={(file) => addCapacity(study.id, file)} />
            )
          }
        />
      )}

      {openModal && (
        <CreateCandidateModal
          open={openModal}
          onClose={onClose}
          onSave={createCandidate}
          links={links || []}
        />
      )}
      {!!singleConstraint && (
        <XpansionTableModal
          open={!!singleConstraint}
          title={singleConstraint.filename}
          handleClose={() => setSingleConstraint(undefined)}
        >
          <code style={{ whiteSpace: 'pre' }}>{singleConstraint.content}</code>
        </XpansionTableModal>
      )}
      {!!singleCapa && (
        <XpansionTableModal
          open={!!singleCapa}
          title={singleCapa.filename}
          handleClose={() => setSingleCapa(undefined)}
        >
          <MatrixView
            matrix={singleCapa.content}
            readOnly
          />
        </XpansionTableModal>
      )}
    </>
  );
};

export default XpansionView;
