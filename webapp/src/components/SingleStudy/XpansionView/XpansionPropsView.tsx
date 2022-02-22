import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
} from '@material-ui/core';
import PropertiesView from '../../ui/PropertiesView';
import { XpansionCandidate, XpansionSettings } from './types';
import CandidateListing from './CandidateListing';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    list: {
      display: 'flex',
      justifyContent: 'flex-start',
      alignItems: 'center',
      flexDirection: 'column',
      padding: theme.spacing(1),
      flexGrow: 1,
      marginBottom: '76px',
      width: '94%',
    },
  }));

interface PropsType {
  candidateList: Array<XpansionCandidate>;
  settings: XpansionSettings | undefined;
  constraints: string;
  selectedItem: XpansionCandidate | XpansionSettings | string | undefined;
  setSelectedItem: (item: XpansionCandidate | XpansionSettings | string) => void;
  onAdd: () => void;
  deleteXpansion: () => void;
}

const XpansionPropsView = (props: PropsType) => {
  const classes = useStyles();
  const { candidateList, settings, constraints, selectedItem, setSelectedItem, onAdd, deleteXpansion } = props;
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
    <>
      <PropertiesView
        content={
          !filteredCandidates && (
          <div className={classes.list}>
            <CandidateListing candidates={candidateList} settings={settings} constraints={constraints} selectedItem={selectedItem} setSelectedItem={setSelectedItem} deleteXpansion={deleteXpansion} />
          </div>
          )}
        filter={
          filteredCandidates && (
          <div className={classes.list}>
            <CandidateListing candidates={filteredCandidates} settings={settings} constraints={constraints} selectedItem={selectedItem} setSelectedItem={setSelectedItem} deleteXpansion={deleteXpansion} />
          </div>
          )}
        onChange={(e) => onChange(e as string)}
        onAdd={onAdd}
      />
    </>
  );
};

export default XpansionPropsView;
