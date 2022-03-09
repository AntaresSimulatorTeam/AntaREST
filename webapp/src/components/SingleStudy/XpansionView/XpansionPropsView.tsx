import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  Box,
  Button,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import PropertiesView from '../../ui/PropertiesView';
import { XpansionCandidate, XpansionSettings } from './types';
import CandidateListing from './CandidateListing';
import ConfirmationModal from '../../ui/ConfirmationModal';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    list: {
      position: 'unset',
      display: 'flex',
      justifyContent: 'flex-start',
      alignItems: 'flex-end',
      flexDirection: 'column',
      padding: theme.spacing(1),
      flexGrow: 1,
      marginBottom: '76px',
      width: '94%',
    },
    buttons: {
      position: 'absolute',
      bottom: '20px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'flex-end',
      color: theme.palette.secondary.dark,
    },
    button: {
      color: theme.palette.primary.main,
    },
    delete: {
      color: theme.palette.error.main,
    },
  }));

interface PropsType {
  candidateList?: Array<XpansionCandidate>;
  settings: XpansionSettings | undefined;
  constraints: Array<string> | undefined;
  capacities: Array<string> | undefined;
  selectedItem: XpansionCandidate | XpansionSettings | Array<string> | undefined;
  setSelectedItem: (item: XpansionCandidate | XpansionSettings | Array<string>) => void;
  onAdd: () => void;
  deleteXpansion: () => void;
}

const XpansionPropsView = (props: PropsType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { candidateList, settings, constraints, capacities, selectedItem, setSelectedItem, onAdd, deleteXpansion } = props;
  const [filteredCandidates, setFilteredCandidates] = useState<Array<XpansionCandidate>>();
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);

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
          <Box className={classes.list}>
            <CandidateListing candidates={candidateList} selectedItem={selectedItem} setSelectedItem={setSelectedItem} />
            <Box className={classes.buttons}>
              <Button className={classes.button} size="small" onClick={() => { if (settings) { setSelectedItem(settings); } }}>{t('main:settings')}</Button>
              <Button className={classes.button} size="small" onClick={() => { if (constraints) { setSelectedItem(constraints); } }}>{t('main:files')}</Button>
              <Button className={classes.button} size="small" onClick={() => { if (capacities) { setSelectedItem(capacities); } }}>{t('xpansion:capacities')}</Button>
              <Button className={classes.delete} size="small" onClick={() => setOpenConfirmationModal(true)}>{t('main:delete')}</Button>
            </Box>
          </Box>
          )}
        filter={
          filteredCandidates && (
          <Box className={classes.list}>
            <CandidateListing candidates={filteredCandidates} selectedItem={selectedItem} setSelectedItem={setSelectedItem} />
            <Box className={classes.buttons}>
              <Button className={classes.button} size="small" onClick={() => { if (settings) { setSelectedItem(settings); } }}>{t('main:settings')}</Button>
              <Button className={classes.button} size="small" onClick={() => { if (constraints) { setSelectedItem(constraints); } }}>{t('main:files')}</Button>
              <Button className={classes.button} size="small" onClick={() => { if (capacities) { setSelectedItem(capacities); } }}>{t('xpansion:capacities')}</Button>
              <Button className={classes.delete} size="small" onClick={() => setOpenConfirmationModal(true)}>{t('main:delete')}</Button>
            </Box>
          </Box>
          )}
        onChange={(e) => onChange(e as string)}
        onAdd={onAdd}
      />
      {openConfirmationModal && candidateList && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={t('xpansion:confirmDeleteXpansion')}
          handleYes={() => { deleteXpansion(); setOpenConfirmationModal(false); }}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
    </>
  );
};

XpansionPropsView.defaultProps = {
  candidateList: undefined,
};

export default XpansionPropsView;
