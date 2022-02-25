import React, { useCallback, useEffect, useState } from 'react';
import { AxiosError } from 'axios';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { Box, Button } from '@material-ui/core';
import XpansionPropsView from './XpansionPropsView';
import { StudyMetadata } from '../../../common/types';
import SplitLayoutView from '../../ui/SplitLayoutView';
import CreateCandidateModal from './CreateCandidateModal';
import { XpansionCandidate, XpansionSettings } from './types';
import XpansionForm from './XpansionForm';
import { getAllCandidates, getXpansionSettings, xpansionConfigurationExist, getAllConstraints, getAllCapacities, createXpansionConfiguration, deleteXpansionConfiguration, addCandidate, deleteCandidate } from '../../../services/api/xpansion';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';
import { getAllLinks } from '../../../services/api/studydata';
import { LinkCreationInfo } from '../MapView/types';
import SimpleLoader from '../../ui/loaders/SimpleLoader';

interface Props {
    study: StudyMetadata;
}

const XpansionView = (props: Props) => {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { study } = props;
  const [openModal, setOpenModal] = useState<boolean>(false);
  const [selectedItem, setSelectedItem] = useState<XpansionCandidate | XpansionSettings | Array<string>>();
  const [settings, setSettings] = useState<XpansionSettings>();
  const [candidates, setCandidates] = useState<Array<XpansionCandidate>>();
  const [constraints, setConstraints] = useState<Array<string>>();
  const [links, setLinks] = useState<Array<LinkCreationInfo>>();
  const [capacities, setCapacities] = useState<Array<string>>();
  // state pour savoir si créer ou nom
  const [createConfigView, setCreateConfigView] = useState<boolean>(false);
  const [loaded, setLoaded] = useState<boolean>(false);

  const init = useCallback(async (after: () => void = () => { /* noop */ }) => {
    try {
      const exist = await xpansionConfigurationExist(study.id);
      if (exist) {
        const tempSettings = await getXpansionSettings(study.id);
        setSettings(tempSettings);
        const tempCandidates = await getAllCandidates(study.id);
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
      enqueueErrorSnackbar(enqueueSnackbar, 'marche pas', e as AxiosError);
    } finally {
      setLoaded(true);
    }
  }, [study.id, enqueueSnackbar]);

  const handleCreate = async () => {
    try {
      await createXpansionConfiguration(study.id);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, 'marche pas', e as AxiosError);
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
      enqueueErrorSnackbar(enqueueSnackbar, 'marche pas', e as AxiosError);
    } finally {
      setCreateConfigView(true);
    }
  };

  const createCandidate = async (name: string, link: string) => {
    try {
      // eslint-disable-next-line @typescript-eslint/camelcase
      await addCandidate(study.id, { name, link, 'annual-cost-per-mw': 0, 'max-investment': 0 });
      setOpenModal(false);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, 'marche pas', e as AxiosError);
    } finally {
      init(() => setSelectedItem({ name, link, 'annual-cost-per-mw': 0, 'max-investment': 0 }));
    }
  };

  const handleDeleteCandidate = async (name: string) => {
    if (candidates) {
      const obj = candidates.filter((o) => o.name !== name);
      try {
        setCandidates(obj);
        setSelectedItem(undefined);
        await deleteCandidate(study.id, name);
      } catch (e) {
        setSelectedItem(candidates.find((o) => o.name === name));
        setCandidates([...candidates]);
        enqueueErrorSnackbar(enqueueSnackbar, 'marche pas', e as AxiosError);
      } finally {
        init();
      }
    }
  };

  const updateCandidate = (value: XpansionCandidate) => {
    console.log(value.name);
    console.log('on a edit un commit');
  };

  const updateSettings = (value: XpansionSettings) => {
    console.log(value.master);
  };

  useEffect(() => {
    init();
  }, [init]);

  const onClose = () => setOpenModal(false);

  return (
    <>
      {loaded ? createConfigView && (
        <Box>
          <Button onClick={handleCreate}>Créer</Button>
        </Box>
      ) : (
        <SimpleLoader />
      )}
      {loaded && !createConfigView && (
        <SplitLayoutView
          title={t('singlestudy:xpansion')}
          left={
            <XpansionPropsView candidateList={candidates} settings={settings} constraints={constraints} capacities={capacities} onAdd={() => setOpenModal(true)} selectedItem={selectedItem} setSelectedItem={setSelectedItem} deleteXpansion={deleteXpansion} />
          }
          right={
            selectedItem && (
              <XpansionForm selectedItem={selectedItem} links={links || []} constraints={constraints} capacities={capacities} deleteCandidate={handleDeleteCandidate} updateCandidate={updateCandidate} updateSettings={updateSettings} />
            )
          }
        />
      )}

      {openModal && (
        <CreateCandidateModal
          open={openModal}
          onClose={onClose}
          onSave={createCandidate}
        />
      )}
    </>
  );
};

export default XpansionView;
