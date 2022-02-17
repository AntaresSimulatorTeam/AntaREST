import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import XpansionPropsView from './XpansionPropsView';
import { StudyMetadata } from '../../../common/types';
import SplitLayoutView from '../../ui/SplitLayoutView';
import CreateCandidateModal from './CreateCandidateModal';
import mockdata from './mockdata.json';
import { XpansionCandidate } from './types';
import CandidateForm from './CandidateForm';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      color: theme.palette.primary.main,
    },
  }));

interface Props {
    study: StudyMetadata;
}

const XpansionView = (props: Props) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { study } = props;
  const [openModal, setOpenModal] = useState<boolean>(false);
  const [selectedItem, setSelectedItem] = useState<XpansionCandidate>();

  const createCandidate = (name: string) => {
    setOpenModal(false);
    console.log(study.id);
    console.log(name);
  };

  const deleteCandidate = (name: string) => {
    console.log(name);
  };

  const updateCandidate = (value: XpansionCandidate) => {
    console.log(study.id);
    console.log(value.name);
  };

  const onClose = () => setOpenModal(false);

  return (
    <>
      <SplitLayoutView
        title={t('singlestudy:xpansion')}
        left={
          <XpansionPropsView candidateList={mockdata} onAdd={() => setOpenModal(true)} selectedItem={selectedItem} setSelectedItem={setSelectedItem} />
        }
        right={
          selectedItem && (
            <CandidateForm candidate={selectedItem} deleteCandidate={deleteCandidate} updateCandidate={updateCandidate} />
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
