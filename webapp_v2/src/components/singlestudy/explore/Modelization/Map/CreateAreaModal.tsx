import React, { useState } from 'react';
import {
  Box,
  TextField,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { isStringEmpty } from '../../../../../services/utils';
import BasicModal from '../../../../common/BasicModal';

interface PropType {
    open: boolean;
    onClose: () => void;
    onSave: (name: string, posX: number, posY: number, color: string) => void;
}

const DEFAULT_COLOR = 'rgb(230, 108, 44)';
const DEFAULT_X = 0;
const DEFAULT_Y = 0;

function CreateAreaModal(props: PropType) {
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
    <BasicModal
      title={t('singlestudy:newArea')}
      open={open}
      onClose={onClose}
      closeButtonLabel={t('settings:cancelButton')}
      actionButtonLabel={t('settings:saveButton')}
      onActionButtonClick={() => handleSave(name, DEFAULT_X, DEFAULT_Y, DEFAULT_COLOR)}
      rootStyle={{ maxWidth: '80%', maxHeight: '70%', display: 'flex', flexFlow: 'column nowrap', alignItems: 'center' }}
    >
      <Box sx={{ m: 2 }}>
        <TextField
          label={t('main:name')}
          variant="outlined"
          onChange={(event) => setName(event.target.value as string)}
          value={name}
          size="small"
        />
      </Box>
    </BasicModal>
  );
}

export default CreateAreaModal;
