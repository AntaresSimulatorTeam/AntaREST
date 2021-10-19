/* eslint-disable @typescript-eslint/camelcase */
import React, { useState, useEffect } from 'react';
import { createStyles, makeStyles, TextField, Select, InputLabel, MenuItem, InputAdornment, Theme } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import MailIcon from '@material-ui/icons/Mail';
import GenericModal from '../ui/GenericModal';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flex: '1',
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    overflowY: 'auto',
    overflowX: 'hidden',
  },
  input: {

  },
  form: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'left',
    flexDirection: 'column',
    height: '220px',
    padding: '20px 20px',
  },
  select: {
    display: 'flex',
    flexDirection: 'row',
  },
  label: {
    transformOrigin: 'center',
    width: '160px',
    padding: '5px',
    lineHeight: 'unset',
  },
  icon: {
    color: theme.palette.primary.main,
  },
}));

interface PropTypes {
    open: boolean;
    onClose: () => void;
}

const HelpModal = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { open, onClose } = props;

  const onSave = async () => {
    console.log('save');
  };

  return (
    <GenericModal
      open={open}
      handleClose={onClose}
      handleSave={onSave}
      title={t('main:helpmodal')}
    >
      <div className={classes.root}>
        <form className={classes.form}>
          <TextField
            required
            className={classes.input}
            placeholder={t('main:mail')}
            InputProps={{ startAdornment: (<InputAdornment position="start"><MailIcon className={classes.icon} /></InputAdornment>) }}
          />
          <div className={classes.select}>
            <InputLabel required className={classes.label} id="label">{t('main:issue')}</InputLabel>
            <Select labelId="label" id="select" value="1">
              <MenuItem value="1">Issue 1</MenuItem>
              <MenuItem value="2">Issue 2</MenuItem>
            </Select>
          </div>
          <TextField
            required
            id="outlined-multiline-static"
            label={t('main:comment')}
            multiline
            rows={4}
            variant="outlined"
          />
        </form>
      </div>
    </GenericModal>
  );
};

export default HelpModal;
