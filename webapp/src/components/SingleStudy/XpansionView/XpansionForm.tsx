import React from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
} from '@material-ui/core';
import { XpansionCandidate, XpansionSettings } from './types';
import CandidateForm from './CandidateForm';
import SettingsForm from './SettingsForm';
import { LinkCreationInfo } from '../MapView/types';
import ConstraintsView from './ConstraintsView';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    form: {
      width: '100%',
      height: '40%',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      flexWrap: 'wrap',
      padding: theme.spacing(1),
    },
    constraints: {
      width: '100%',
      height: '100%',
      display: 'flex',
      overflow: 'hidden',
      flexGrow: 1,
      padding: theme.spacing(1),
    },
  }));

interface PropType {
    selectedItem: XpansionCandidate | XpansionSettings | Array<string> | undefined;
    links: Array<LinkCreationInfo>;
    deleteCandidate: (name: string) => void;
    updateCandidate: (value: XpansionCandidate) => void;
    updateSettings: (value: XpansionSettings) => void;
}

const XpansionForm = (props: PropType) => {
  const classes = useStyles();
  const { selectedItem, links, deleteCandidate, updateCandidate, updateSettings } = props;

  return (
    <>
      {(selectedItem as XpansionCandidate).name || (selectedItem as XpansionSettings).master ? (
        <div className={classes.form}>
          {selectedItem && (selectedItem as XpansionCandidate).name && (
            <CandidateForm candidate={selectedItem as XpansionCandidate} links={links} deleteCandidate={deleteCandidate} updateCandidate={updateCandidate} />
          )}
          {selectedItem && (selectedItem as XpansionSettings).master && (
            <SettingsForm settings={selectedItem as XpansionSettings} updateSettings={updateSettings} />
          )}
        </div>
      ) : (
        <div className={classes.constraints}>
          {Object.keys(selectedItem as Array<string>).map((item, index) => (selectedItem as Array<string>)[index]).length >= 0 && (
            <ConstraintsView content={selectedItem as Array<string>} />
          )}
        </div>
      )}
    </>
  );
};

export default XpansionForm;
