/* eslint-disable @typescript-eslint/camelcase */
import React, { useState } from 'react';
import { createStyles, makeStyles, Theme, TextField } from '@material-ui/core';
import Autocomplete from '@material-ui/lab/Autocomplete';
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
    onNewCommand: (action: string) => void;
    onClose: () => void;
}

const AddCommandModal = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { open, onNewCommand, onClose } = props;
  const [action, setAction] = useState<string>(CommandList[0]);

  const onSave = async () => {
    onNewCommand(action);
    onClose();
  };

  return (
    <GenericModal
      open={open}
      handleClose={onClose}
      handleSave={onSave}
      title={t('variants:newCommand')}
    >
      <div className={classes.infos}>
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
