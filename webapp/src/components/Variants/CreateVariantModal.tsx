/* eslint-disable @typescript-eslint/camelcase */
import React, { useState } from 'react';
import { AxiosError } from 'axios';
import { createStyles, makeStyles, Theme, TextField } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { useHistory } from 'react-router-dom';
import GenericModal from '../ui/GenericModal';
import { createVariant } from '../../services/api/variant';
import enqueueErrorSnackbar from '../ui/ErrorSnackBar';

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

const CreateVariantModal = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const history = useHistory();
  const { enqueueSnackbar } = useSnackbar();
  const { open, parentId, onClose } = props;
  const [name, setName] = useState<string>('');

  const onSave = async () => {
    try {
      const newId = await createVariant(parentId, name);
      setName('');
      onClose();
      history.push(`/study/${newId}/variants/edition`);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('variants:onVariantCreationError'), e as AxiosError);
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

export default CreateVariantModal;
