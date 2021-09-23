/* eslint-disable @typescript-eslint/camelcase */
import React, { useState } from 'react';
import { createStyles, makeStyles, Theme, TextField } from '@material-ui/core';
import Autocomplete from '@material-ui/lab/Autocomplete';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import GenericModal from '../../ui/GenericModal';
import { CommandList } from './utils';

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
  autocomplete: {
    width: '100%',
    height: '30px',
    boxSizing: 'border-box',
  },
  idFields: {
    width: '70%',
    height: '30px',
    boxSizing: 'border-box',
    margin: theme.spacing(2.5, 1),
  },
}));

interface PropTypes {
    open: boolean;
    onNewCommand: (name: string, action: string) => void;
    onClose: () => void;
}

const AddCommandModal = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { open, onNewCommand, onClose } = props;
  const [name, setName] = useState<string>('');
  const [action, setAction] = useState<string>(CommandList[0]);

  const onSave = async () => {
    onNewCommand(name, action);
    onClose();
    enqueueSnackbar(t('variants:onNewCommandAdded'), { variant: 'success' });
  };

  return (
    <GenericModal
      open={open}
      handleClose={onClose}
      handleSave={onSave}
      title={t('variants:newCommand')}
    >
      <div className={classes.infos}>
        <TextField
          className={classes.idFields}
          value={name}
          onChange={(event) => setName(event.target.value as string)}
          label={t('variants:commandNameLabel')}
          variant="outlined"
        />
        <Autocomplete
          options={CommandList}
          getOptionLabel={(option) => option}
          value={action || null}
          className={classes.idFields}
          onChange={(event: any, newValue: string | null) => setAction(newValue !== null ? newValue : CommandList[0])}
          renderInput={(params) => (
            <TextField
          // eslint-disable-next-line react/jsx-props-no-spreading
              {...params}
              className={classes.autocomplete}
              size="small"
              label={t('variants:commandActionLabel')}
              variant="outlined"
            />
          )}
        />
      </div>
    </GenericModal>
  );
};

export default AddCommandModal;
