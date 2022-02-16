import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
} from '@material-ui/core';
import PropertiesView from '../../ui/PropertiesView';
import { XpansionCandidate } from './types';
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
  setSelectedItem: (item: XpansionCandidate) => void;
  onAdd: () => void;
}

const XpansionPropsView = (props: PropsType) => {
  const classes = useStyles();
  const { candidateList, setSelectedItem, onAdd } = props;
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
        content={!filteredCandidates && (
          <div className={classes.list}>
            <CandidateListing candidates={candidateList} setSelectedItem={setSelectedItem} />
          </div>
        )}
        filter={
          filteredCandidates && (
          <CandidateListing candidates={filteredCandidates} setSelectedItem={setSelectedItem} />
          )
        }
        onChange={(e) => onChange(e as string)}
        onAdd={onAdd}
      />
    </>
  );
};

export default XpansionPropsView;
