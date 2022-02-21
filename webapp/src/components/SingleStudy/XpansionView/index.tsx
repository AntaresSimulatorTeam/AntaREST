import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import XpansionPropsView from './XpansionPropsView';
import { StudyMetadata } from '../../../common/types';
import SplitLayoutView from '../../ui/SplitLayoutView';
import CreateCandidateModal from './CreateCandidateModal';
import fakeCandidates from './mockdata.json';
import { XpansionCandidate, XpansionSettings } from './types';
import XpansionForm from './XpansionForm';

interface Props {
    study: StudyMetadata;
}

const fakeConstraints = `<?xml version="1.0" encoding="UTF-8"?>
<richtext version="1.0.0.0" xmlns="http://www.wxwidgets.org">
  <paragraphlayout textcolor="#000000" fontpointsize="9" fontfamily="70" fontstyle="90" fontweight="90" fontunderlined="0" fontface="Segoe UI" alignment="1" parspacingafter="10" parspacingbefore="0" linespacing="10" margin-left="5,4098" margin-right="5,4098" margin-top="5,4098" margin-bottom="5,4098">
    <paragraph>
      <text></text>
    </paragraph>
  </paragraphlayout>
</richtext>
`;

const fakeSettings = {
  // eslint-disable-next-line @typescript-eslint/camelcase
  uc_type: 'uc_type',
  master: 'master',
  // eslint-disable-next-line @typescript-eslint/camelcase
  optimaly_gap: 1,
  // eslint-disable-next-line @typescript-eslint/camelcase
  max_iteration: 1,
  // eslint-disable-next-line @typescript-eslint/camelcase
  yearly_weight: 'yearly_weight',
  // eslint-disable-next-line @typescript-eslint/camelcase
  additional_constraints: 'additional_constraints',
  // eslint-disable-next-line @typescript-eslint/camelcase
  relaxed_optimality_gap: 1,
  // eslint-disable-next-line @typescript-eslint/camelcase
  cut_type: 'cut_type',
  // eslint-disable-next-line @typescript-eslint/camelcase
  ampl_solver: 'ampl_solver',
  // eslint-disable-next-line @typescript-eslint/camelcase
  ampl_presolve: 1,
  // eslint-disable-next-line @typescript-eslint/camelcase
  ampl_solve_bounds_frequency: 1,
  // eslint-disable-next-line @typescript-eslint/camelcase
  relative_gap: 1,
  solver: 'solver',
};

const XpansionView = (props: Props) => {
  const [t] = useTranslation();
  const { study } = props;
  const [openModal, setOpenModal] = useState<boolean>(false);
  const [selectedItem, setSelectedItem] = useState<XpansionCandidate | XpansionSettings>();

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

  const onClose = () => setOpenModal(false);

  return (
    <>
      <SplitLayoutView
        title={t('singlestudy:xpansion')}
        left={
          <XpansionPropsView candidateList={fakeCandidates} settings={fakeSettings} constraints={fakeConstraints} onAdd={() => setOpenModal(true)} selectedItem={selectedItem} setSelectedItem={setSelectedItem} deleteXpansion={deleteXpansion} />
        }
        right={
          selectedItem && (
            <XpansionForm selectedItem={selectedItem} deleteCandidate={deleteCandidate} updateCandidate={updateCandidate} updateSettings={updateSettings} />
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
