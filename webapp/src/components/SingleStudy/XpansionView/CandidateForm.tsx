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
      width: '60%',
      height: '40%',
      display: 'flex',
      justifyContent: 'space-evenly',
      alignItems: 'center',
      flexWrap: 'wrap',
      padding: theme.spacing(1),
    },
    fields: {
      marginTop: theme.spacing(1),
    },
    deleteIcon: {
      cursor: 'pointer',
      color: theme.palette.error.light,
      '&:hover': {
        color: theme.palette.error.main,
      },
    },
    buttons: {
      width: '100%',
      justifyContent: 'flex-end',
      alignItems: 'center',
      display: 'flex',
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
  const { candidate, deleteCandidate, updateCandidate} = props;
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);

  console.log('render');

  return (
    <>
      <div className={classes.form}>
        {candidate && (
          <>
            <TextField className={classes.fields} label="name" variant="filled" value={candidate.name} />
            <TextField className={classes.fields} label="link" variant="filled" value={candidate.link} />
            <TextField className={classes.fields} label="annual_cost_per_mw" variant="filled" value={candidate.annual_cost_per_mw} />
            <TextField className={classes.fields} label="unit_size" variant="filled" value={candidate.unit_size || 0} />
            <TextField className={classes.fields} label="max_units" variant="filled" value={candidate.max_units || 0} />
            <TextField className={classes.fields} label="max_investment" variant="filled" value={candidate.max_investment || 0} />
            <TextField className={classes.fields} label="already_installed_capacity" variant="filled" value={candidate.already_installed_capacity || 0} />
            <TextField className={classes.fields} label="link_profile" variant="filled" value={candidate.link_profile || ''} />
            <TextField className={classes.fields} label="already_installed_link_profile" variant="filled" value={candidate.already_installed_link_profile || ''} />
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
