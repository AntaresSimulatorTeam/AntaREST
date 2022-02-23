import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  TextField,
  Box,
  Divider,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import DeleteIcon from '@material-ui/icons/Delete';
import ConfirmationModal from '../../ui/ConfirmationModal';
import { XpansionCandidate } from './types';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    title: {
      color: theme.palette.primary.main,
    },
    fields: {
      display: 'flex',
      justifyContent: 'flex-start',
      alignItems: 'center',
      width: '100%',
      flexWrap: 'wrap',
      marginBottom: theme.spacing(2),
      '&> div': {
        marginRight: theme.spacing(2),
      },
    },
    deleteIcon: {
      cursor: 'pointer',
      color: theme.palette.error.light,
      '&:hover': {
        color: theme.palette.error.main,
      },
    },
    buttons: {
      position: 'absolute',
      right: '20px',
      bottom: '20px',
    },
    divider: {
      marginTop: theme.spacing(1),
      marginBottom: theme.spacing(1),
    },
  }));

interface PropType {
    candidate: XpansionCandidate;
    deleteCandidate: (name: string) => void;
    updateCandidate: (value: XpansionCandidate) => void;
}

const CandidateForm = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { candidate, deleteCandidate, updateCandidate } = props;
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);

  return (
    <Box>
      <Box>
        <div className={classes.title}>
          Général
        </div>
        <Divider className={classes.divider} />
        <div className={classes.fields}>
          <TextField label="name" variant="filled" value={candidate.name} onBlur={() => updateCandidate(candidate)} />
          <TextField label="link" variant="filled" value={candidate.link} onBlur={() => updateCandidate(candidate)} />
        </div>
      </Box>
      <Box>
        <div className={classes.title}>
          Paramètres
        </div>
        <Divider className={classes.divider} />
        <div className={classes.fields}>
          <TextField label="annual_cost_per_mw" variant="filled" value={candidate.annual_cost_per_mw} onBlur={() => updateCandidate(candidate)} />
          <TextField label="unit_size" variant="filled" value={candidate.unit_size || ''} onBlur={() => updateCandidate(candidate)} />
          <TextField label="max_units" variant="filled" value={candidate.max_units || ''} onBlur={() => updateCandidate(candidate)} />
          <TextField label="max_investment" variant="filled" value={candidate.max_investment || ''} onBlur={() => updateCandidate(candidate)} />
          <TextField label="already_installed_capacity" variant="filled" value={candidate.already_installed_capacity || ''} onBlur={() => updateCandidate(candidate)} />
          <TextField label="already_installed_link_profile" variant="filled" value={candidate.already_installed_link_profile || ''} onBlur={() => updateCandidate(candidate)} />
        </div>
      </Box>
      <Box>
        <div className={classes.title}>
          Time series
        </div>
        <Divider className={classes.divider} />
        <div className={classes.fields}>
          <TextField label="link_profile" variant="filled" value={candidate.link_profile || ''} onBlur={() => updateCandidate(candidate)} />
        </div>
      </Box>
      <div className={classes.buttons}>
        <DeleteIcon className={classes.deleteIcon} onClick={() => setOpenConfirmationModal(true)} />
      </div>
      {openConfirmationModal && candidate && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message="Êtes-vous sûr de vouloir supprimer ce candidat?"
          handleYes={() => { deleteCandidate(candidate.name); setOpenConfirmationModal(false); }}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
    </Box>
  );
};

export default CandidateForm;
