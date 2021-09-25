/* eslint-disable @typescript-eslint/camelcase */
import React, { useState } from 'react';
import { createStyles, makeStyles, Theme, TextField } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import GenericModal from '../ui/GenericModal';

const useStyles = makeStyles((theme: Theme) => createStyles({
  infos: {
    flex: '1',
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing(2),
  },
  nameField: {
    height: '30px',
  },
}));

interface PropTypes {
    open: boolean;
    defaultName: string;
    onNewName: (action: string) => void;
    onClose: () => void;
}

const RenameModal = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { open, defaultName, onNewName, onClose } = props;
  const [name, setName] = useState<string>(defaultName);

  const onSave = async () => {
    onNewName(name);
    onClose();
  };

  return (
    <GenericModal
      open={open}
      handleClose={onClose}
      handleSave={onSave}
      title={t('singlestudy:renamestudy')}
    >
      <div className={classes.infos}>
        <TextField
          defaultValue={defaultName}
          className={classes.nameField}
          size="small"
          onChange={(event) => setName(event.target.value)}
          label={t('studymanager:nameofstudy')}
          variant="outlined"
        />
      </div>
    </GenericModal>
  );
};

export default RenameModal;
