import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import PropertiesView from '../../ui/PropertiesView';
import { XpansionCandidate } from './types';
import CandidateListing from './CandidateListing';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
  }));

interface PropsType {
  candidateList: Array<XpansionCandidate>;
  setSelectedItem: (item: XpansionCandidate) => void;
  onAdd: () => void;
}

const XpansionPropsView = (props: PropsType) => {
  const classes = useStyles();
  const { candidateList, setSelectedItem, onAdd } = props;
  const [t] = useTranslation();
  const [filteredCandidates, setFilteredCandidates] = useState<Array<XpansionCandidate>>();

  const filter = (currentName: string): XpansionCandidate[] => {
    if (candidateList) {
      return candidateList.filter((item) => !currentName || (item.name.search(new RegExp(currentName, 'i')) !== -1));
    }
    return [];
  };

  const onChange = async (currentName: string) => {
    if (currentName !== '') {
      const f = filter(currentName);
      setFilteredCandidates(f);
    } else {
      setFilteredCandidates(undefined);
    }
  };

  return (
    <PropertiesView
      content={!filteredCandidates && (
        <CandidateListing candidates={candidateList} setSelectedItem={setSelectedItem} />
      )}
      filter={
        filteredCandidates && (
        <CandidateListing candidates={filteredCandidates} setSelectedItem={setSelectedItem} />
        )
      }
      onChange={(e) => onChange(e as string)}
      onAdd={onAdd}
    />
  );
};

export default XpansionPropsView;
