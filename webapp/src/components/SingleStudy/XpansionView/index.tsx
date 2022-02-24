import React, { useCallback, useEffect, useState } from 'react';
import { AxiosError } from 'axios';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import XpansionPropsView from './XpansionPropsView';
import { StudyMetadata } from '../../../common/types';
import SplitLayoutView from '../../ui/SplitLayoutView';
import CreateCandidateModal from './CreateCandidateModal';
import { XpansionCandidate, XpansionSettings } from './types';
import XpansionForm from './XpansionForm';
import { getAllCandidates, getXpansionSettings, xpansionConfigurationExist, getAllConstraints } from '../../../services/api/xpansion';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';
import { getAllLinks } from '../../../services/api/studydata';
import { LinkCreationInfo } from '../MapView/types';

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
  // state pour savoir si créer ou nom

  const init = useCallback(async () => {
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
      } else {
        console.log('faut créer');
      }
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, 'marche pas', e as AxiosError);
    }
  }, [study.id, enqueueSnackbar]);

  /*
  const handleCreate = () => {
    try {
      const create = createXpansionConfiguration(study.id);
      // state faut plus créer //  init()
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, 'marche pas', e as AxiosError);
    }
  }; */

  const deleteXpansion = () => {
    console.log('delete');
  };

  const createCandidate = (name: string) => {
    setOpenModal(false);
    console.log(study.id);
    console.log(name);
  };

  const deleteCandidate = (name: string) => {
    console.log(name);
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
      <SplitLayoutView
        title={t('singlestudy:xpansion')}
        left={
          <XpansionPropsView candidateList={candidates} settings={settings} constraints={constraints} onAdd={() => setOpenModal(true)} selectedItem={selectedItem} setSelectedItem={setSelectedItem} deleteXpansion={deleteXpansion} />
        }
        right={
          selectedItem && (
            <XpansionForm selectedItem={selectedItem} links={links || []} deleteCandidate={deleteCandidate} updateCandidate={updateCandidate} updateSettings={updateSettings} />
          )
        }
      />
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
