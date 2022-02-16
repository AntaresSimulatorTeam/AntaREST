import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  TextField,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import GenericModal from '../../ui/GenericModal';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    name: {
      margin: theme.spacing(2),
    },
  }));

interface PropType {
    open: boolean;
    onClose: () => void;
    onSave: (name: string) => void;
}

const CreateCandidateModal = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { open, onClose, onSave } = props;
  const [name, setName] = useState<string>('');

  return (
    <GenericModal
      open={open}
      handleClose={onClose}
      handleAction={() => onSave(name)}
      title="Nouveau candidat"
    >
      <div className={classes.name}>
        <TextField
          label={t('main:name')}
          variant="outlined"
          onChange={(event) => setName(event.target.value as string)}
          value={name}
          size="small"
        />
      </div>
    </GenericModal>
  );
};

export default CreateCandidateModal;
