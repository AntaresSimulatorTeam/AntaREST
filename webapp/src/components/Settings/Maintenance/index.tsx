/* eslint-disable @typescript-eslint/camelcase */
import React, { useEffect, useState } from 'react';
import { createStyles, makeStyles, Theme, TextField, Switch, Typography } from '@material-ui/core';
import { AxiosError } from 'axios';
import { connect, ConnectedProps } from 'react-redux';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import SaveIcon from '@material-ui/icons/Save';
import { AppState } from '../../../App/reducers';
import ConfirmationModal from '../../ui/ConfirmationModal';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';
import { updateMaintenanceMode, updateMessageInfo } from '../../../services/api/maintenance';
import { setMaintenanceMode, setMessageInfo } from '../../../ducks/global';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    width: '80%',
    height: '90%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    color: theme.palette.primary.main,
    // margin: theme.spacing(4),
    padding: theme.spacing(3, 1),
    // backgroundColor: 'red',
  },
  main: {
    width: '600px',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    borderRadius: theme.shape.borderRadius,
    border: `2px solid ${theme.palette.primary.main}`,
    // backgroundColor: 'green',
    padding: theme.spacing(3),
  },
  container: {
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 0,
    marginBottom: theme.spacing(3),
    // backgroundColor: 'blue',
  },
  message: {
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    marginBottom: theme.spacing(3),
  },
  messageText: {
    fontWeight: 'bold',
  },
  textField: {
    marginTop: theme.spacing(1),
    width: '90%',
  },
  saveIcon: {
    cursor: 'pointer',
    color: theme.palette.primary.main,
    '&:hover': {
      color: theme.palette.secondary.main,
    },
  },
  saveIconDisabled: {
    color: theme.palette.grey[500],
  },
  switch: {
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
  },
}));

const mapState = (state: AppState) => ({
  maintenanceMode: state.global.maintenanceMode,
  messageInfo: state.global.messageInfo,
});

const mapDispatch = ({
  updateMode: setMaintenanceMode,
  updateMessage: setMessageInfo,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const Maintenance = (props: PropTypes) => {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const classes = useStyles();
  const { maintenanceMode, updateMode, messageInfo, updateMessage } = props;
  const [currentMaintenance, setCurrentMaintenance] = useState<boolean>(maintenanceMode);
  const [currentMessage, setCurrentMessage] = useState<string>(messageInfo);
  const [openConfirmationModal, setOpenConfirmationModal] = useState(false);
  const [isMaintenance, setIsMaintenance] = useState(true);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setCurrentMaintenance(event.target.checked);
  };

  const onClick = (maintenance: boolean): void => {
    setIsMaintenance(maintenance);
    setOpenConfirmationModal(true);
  };

  const onMaintenanceSave = async () => {
    try {
      if (currentMaintenance !== maintenanceMode) {
        await updateMaintenanceMode(currentMaintenance);
        updateMode(currentMaintenance);
        enqueueSnackbar(t('settings:onUpdateMaintenance'), { variant: 'success' });
      }
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('settings:onUpdateMaintenanceError'), e as AxiosError);
    }
    setOpenConfirmationModal(false);
  };

  const onMessageSave = async () => {
    try {
      if (currentMessage !== messageInfo) {
        await updateMessageInfo(currentMessage);
        updateMessage(currentMessage);
        enqueueSnackbar(t('settings:onUpdateMessageInfo'), { variant: 'success' });
      }
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('settings:onUpdateMessageInfoError'), e as AxiosError);
    }
    setOpenConfirmationModal(false);
  };

  useEffect(() => {
    console.log('MAINTENANCE MODE: ', maintenanceMode);
    //setCurrentMessage()
  }, [maintenanceMode]);

  return (
    <div className={classes.root}>
      <div className={classes.main}>
        <div className={classes.container}>
          <div className={classes.switch}>
            <Typography className={classes.messageText}>{t('settings:maintenanceMode')}</Typography>
            <Switch
              checked={currentMaintenance}
              onChange={handleChange}
              color="primary"
              name="Maintenance mode"
              inputProps={{ 'aria-label': 'primary checkbox' }}
            />
          </div>
          <SaveIcon
            className={currentMaintenance === maintenanceMode ? classes.saveIconDisabled : classes.saveIcon}
            onClick={currentMaintenance === maintenanceMode ? undefined : () => onClick(true)}
          />
        </div>
        <div className={classes.container}>
          <div className={classes.message}>
            <Typography className={classes.messageText}>{t('settings:messageMode')}</Typography>
            <TextField
              className={classes.textField}
              variant="outlined"
              fullWidth
              label="Message"
              id="fullWidth"
              value={currentMessage !== undefined ? currentMessage : ''}
              onChange={(event) => setCurrentMessage(event.target.value as string)}
            />
          </div>
          <SaveIcon
            className={currentMessage === messageInfo ? classes.saveIconDisabled : classes.saveIcon}
            onClick={currentMessage === messageInfo ? undefined : () => onClick(false)}
          />
        </div>
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={t(isMaintenance ? 'settings:updateMaintenanceModeConfirmation' : 'settings:updateMessageModeConfirmation')}
          handleYes={isMaintenance ? onMaintenanceSave : onMessageSave}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      </div>
    </div>
  );
};

export default connector(Maintenance);
