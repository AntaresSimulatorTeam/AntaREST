import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  TextField,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import GenericModal from '../../ui/GenericModal';
import { isStringEmpty } from '../../../services/utils';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    name: {
      margin: theme.spacing(2),
    },
    positions: {
      margin: theme.spacing(2),
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
    },
    posX: {
      width: '130px',
    },
    posY: {
      width: '130px',
    },
    color: {
      margin: theme.spacing(2),
    },
  }));

interface PropType {
    open: boolean;
    onClose: () => void;
    onSave: (name: string, posX: number, posY: number, color: string) => void;
}

const DEFAULT_COLOR = 'rgb(230, 108, 44)';
const DEFAULT_X = 0;
const DEFAULT_Y = 0;

const CreateAreaModal = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { open, onClose, onSave } = props;
  const [name, setName] = useState<string>('');

  const handleSave = (id: string, posX: number, posY: number, color: string) => {
    if (!isStringEmpty(id)) {
      onSave(id, posX, posY, color);
    } else {
      enqueueSnackbar(t('singlestudy:createAreaError'), { variant: 'error' });
    }
  };

  return (
    <GenericModal
      open={open}
      handleClose={onClose}
      handleAction={() => handleSave(name, DEFAULT_X, DEFAULT_Y, DEFAULT_COLOR)}
      title={t('singlestudy:newArea')}
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

export default CreateAreaModal;
