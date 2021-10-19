/* eslint-disable react-hooks/exhaustive-deps */
import React, { PropsWithChildren, useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { createStyles, makeStyles, Theme, Typography, TextField, Button, ButtonBase } from '@material-ui/core';
import debug from 'debug';
import HelpIcon from '@material-ui/icons/Help';
import HelpModal from '../../components/Help/HelpModal';

const logError = debug('antares:helpwrapper:error');

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      position: 'absolute',
      bottom: '20px',
      right: '20px',
      zIndex: 1000,
    },
    helpButton: {
      width: '150px',
      height: '60px',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'space-between',
      alignItems: 'center',
      borderRadius: '30px',
      backgroundColor: theme.palette.secondary.main,
      padding: '0px 15px',
    },
    helpIcon: {
      color: 'white',
    },
    helpTypo: {
      color: 'white',
    },
  }));

const HelpWrapper = () => {
  const classes = useStyles();
  const [openModal, setOpenModal] = useState<boolean>(false);

  return (
    <div className={classes.root}>
      <HelpModal open={openModal} onClose={() => setOpenModal(false)} />
      <ButtonBase className={classes.helpButton} onClick={() => setOpenModal(true)}>
        <HelpIcon className={classes.helpIcon} />
        <Typography className={classes.helpTypo}>Signal a bug</Typography>
      </ButtonBase>
    </div>
  );
};

export default HelpWrapper;
