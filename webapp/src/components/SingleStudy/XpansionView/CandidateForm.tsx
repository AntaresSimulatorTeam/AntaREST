import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  TextField,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import DeleteIcon from '@material-ui/icons/Delete';
import ConfirmationModal from '../../ui/ConfirmationModal';
import { XpansionCandidate } from './types';

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
    fields: {
      display: 'flex',
      justifyContent: 'space-evenly',
      alignItems: 'center',
      width: '100%',
      flexWrap: 'wrap',
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
  }));

interface PropType {
    candidate?: XpansionCandidate;
    deleteCandidate: (name: string) => void;
    updateCandidate: (value: XpansionCandidate) => void;
}

const CandidateForm = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { candidate, deleteCandidate, updateCandidate } = props;
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);

  return (
    <>
      <div className={classes.form}>
        {candidate && (
          <>
            <div className={classes.fields}>
              <TextField label="name" variant="filled" value={candidate.name} onBlur={() => updateCandidate(candidate)} />
              <TextField label="link" variant="filled" value={candidate.link} onBlur={() => updateCandidate(candidate)} />
              <TextField label="annual_cost_per_mw" variant="filled" value={candidate.annual_cost_per_mw} onBlur={() => updateCandidate(candidate)} />
            </div>
            <div className={classes.fields}>
              <TextField label="unit_size" variant="filled" value={candidate.unit_size || ''} onBlur={() => updateCandidate(candidate)} />
              <TextField label="max_units" variant="filled" value={candidate.max_units || ''} onBlur={() => updateCandidate(candidate)} />
              <TextField label="max_investment" variant="filled" value={candidate.max_investment || ''} onBlur={() => updateCandidate(candidate)} />
            </div>
            <div className={classes.fields}>
              <TextField label="already_installed_capacity" variant="filled" value={candidate.already_installed_capacity || ''} onBlur={() => updateCandidate(candidate)} />
              <TextField label="link_profile" variant="filled" value={candidate.link_profile || ''} onBlur={() => updateCandidate(candidate)} />
              <TextField label="already_installed_link_profile" variant="filled" value={candidate.already_installed_link_profile || ''} onBlur={() => updateCandidate(candidate)} />
            </div>
            <div className={classes.buttons}>
              <DeleteIcon className={classes.deleteIcon} onClick={() => setOpenConfirmationModal(true)} />
            </div>
          </>
        )}
      </div>
      {openConfirmationModal && candidate && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={t('singlestudy:confirmDeleteArea')}
          handleYes={() => { deleteCandidate(candidate.name); setOpenConfirmationModal(false); }}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
    </>
  );
};

CandidateForm.defaultProps = {
  candidate: undefined,
};
export default CandidateForm;
