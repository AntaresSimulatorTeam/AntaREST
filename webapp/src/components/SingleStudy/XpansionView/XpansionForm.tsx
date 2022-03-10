import React from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  Box,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import { XpansionCandidate, XpansionSettings } from './types';
import CandidateForm from './CandidateForm';
import SettingsForm from './SettingsForm';
import { LinkCreationInfo } from '../MapView/types';
import XpansionTable from './XpansionTable';

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
    constraints: Array<string>;
    capacities: Array<string>;
    deleteCandidate: (name: string) => void;
    updateCandidate: (name: string, value: XpansionCandidate) => Promise<void>;
    updateSettings: (value: XpansionSettings) => Promise<void>;
    deleteConstraint: (filename: string) => Promise<void>;
    deleteCapa: (filename: string) => Promise<void>;
    getConstraint: (filename: string) => Promise<void>;
    getCapacity: (filename: string) => Promise<void>;
    addConstraint: (file: File) => Promise<void>;
    addCapacity: (file: File) => Promise<void>;
}

const XpansionForm = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { selectedItem, links, constraints, capacities, deleteCandidate, updateCandidate, updateSettings, deleteConstraint, deleteCapa, getConstraint, getCapacity, addConstraint, addCapacity } = props;

  console.log(selectedItem);
  console.log(constraints);

  return (
    <>
      {(selectedItem as XpansionCandidate).name || (selectedItem as XpansionSettings).master ? (
        <Box className={classes.form}>
          {selectedItem && (selectedItem as XpansionCandidate).name && (
            <CandidateForm candidate={selectedItem as XpansionCandidate} links={links} capacities={capacities} deleteCandidate={deleteCandidate} updateCandidate={updateCandidate} onRead={getCapacity} />
          )}
          {selectedItem && (selectedItem as XpansionSettings).master && (
            <SettingsForm settings={selectedItem as XpansionSettings} constraints={constraints} updateSettings={updateSettings} onRead={getConstraint} />
          )}
        </Box>
      ) : (
        <Box className={classes.constraints}>
          {constraints === selectedItem ? (
            <XpansionTable title={t('main:files')} content={selectedItem as Array<string>} onDelete={deleteConstraint} onRead={getConstraint} uploadFile={addConstraint} />
          ) : (capacities === selectedItem && (
            <XpansionTable title={t('xpansion:capacities')} content={selectedItem as Array<string>} onDelete={deleteCapa} onRead={getCapacity} uploadFile={addCapacity} />
          ))}
        </Box>
      )}
    </>
  );
};

export default XpansionForm;
