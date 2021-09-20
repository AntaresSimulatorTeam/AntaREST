/* eslint-disable @typescript-eslint/camelcase */
import React, { useState } from 'react';
import { createStyles, makeStyles, Theme, TextField } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { useHistory } from 'react-router-dom';
import GenericModal from '../ui/GenericModal';
import { createVariant } from '../../services/api/variant';

const useStyles = makeStyles((theme: Theme) => createStyles({
  infos: {
    flex: '1',
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    padding: theme.spacing(2),
  },
  idFields: {
    width: '70%',
    height: '30px',
    boxSizing: 'border-box',
    margin: theme.spacing(2),
  },
}));

interface PropTypes {
    open: boolean;
    parentId: string;
    onClose: () => void;
}

const VariantModal = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const history = useHistory();
  const { enqueueSnackbar } = useSnackbar();
  const { open, parentId, onClose } = props;
  const [name, setName] = useState<string>('');

  const onSave = async () => {
    try {
      const newId = await createVariant(parentId, name);
      onClose();
      history.push(`/study/${newId}/variants/edition`);
    } catch (e) {
      enqueueSnackbar(t('variants:onVariantCreationError'), { variant: 'error' });
    }
  };

  return (
    <GenericModal
      open={open}
      handleClose={onClose}
      handleSave={onSave}
      title={t('variants:newVariant')}
    >
      <div className={classes.infos}>
        <TextField
          className={classes.idFields}
          value={name}
          onChange={(event) => setName(event.target.value as string)}
          label={t('variants:variantNameLabel')}
          variant="outlined"
        />
      </div>
    </GenericModal>
  );
};

export default VariantModal;
