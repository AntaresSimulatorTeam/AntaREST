import React from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
} from '@material-ui/core';
import { XpansionCandidate, XpansionSettings } from './types';
import CandidateForm from './CandidateForm';
import SettingsForm from './SettingsForm';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    form: {
      width: '90%',
      height: '40%',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      flexWrap: 'wrap',
      padding: theme.spacing(1),
    },
  }));

interface PropType {
    selectedItem: XpansionCandidate | XpansionSettings | undefined;
    deleteCandidate: (name: string) => void;
    updateCandidate: (value: XpansionCandidate) => void;
    updateSettings: (value: XpansionSettings) => void;
}

const XpansionForm = (props: PropType) => {
  const classes = useStyles();
  const { selectedItem, deleteCandidate, updateCandidate, updateSettings } = props;

  return (
    <>
      <div className={classes.form}>
        {selectedItem && (selectedItem as XpansionCandidate).name && (
          <CandidateForm candidate={selectedItem as XpansionCandidate} deleteCandidate={deleteCandidate} updateCandidate={updateCandidate} />
        )}
        {selectedItem && (selectedItem as XpansionSettings).master && (
          <SettingsForm settings={selectedItem as XpansionSettings} updateSettings={updateSettings} />
        )}
      </div>
    </>
  );
};

export default XpansionForm;
