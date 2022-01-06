/* eslint-disable @typescript-eslint/camelcase */
import React, { useState, useEffect } from 'react';
import Radio from '@material-ui/core/Radio';
import RadioGroup from '@material-ui/core/RadioGroup';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import FormControl from '@material-ui/core/FormControl';
import { createStyles, makeStyles, Theme, TextField, Button } from '@material-ui/core';
import { AxiosError } from 'axios';
import { connect, ConnectedProps } from 'react-redux';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { AppState } from '../../../App/reducers';
import ConfirmationModal from '../../ui/ConfirmationModal';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';
import { updateMaintenanceMode } from '../../../services/api/maintenance';
import { MaintenanceDTO, MaintenanceMode } from '../../../common/types';
import { setMaintenanceMode } from '../../../ducks/global';

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
  header: {
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    padding: 0,
    marginBottom: theme.spacing(3),
    // backgroundColor: 'blue',
  },
  radioGroup: {
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
  },
  content: {
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    marginBottom: theme.spacing(3),
  },
  footer: {
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
}));

const mapState = (state: AppState) => ({
  maintenanceMode: state.global.maintenanceMode,
});

const mapDispatch = ({
  updateMode: setMaintenanceMode,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const Maintenance = (props: PropTypes) => {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const classes = useStyles();
  const { maintenanceMode, updateMode } = props;
  const [maintenance, setMaintenance] = useState<MaintenanceDTO>(maintenanceMode);
  const [openConfirmationModal, setOpenConfirmationModal] = useState(false);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setMaintenance({ mode: event.target.value as MaintenanceMode, message: '' });
  };

  const isUpdated = (): boolean => {
    if (maintenance.mode === MaintenanceMode.NORMAL) return maintenanceMode.mode === maintenance.mode;
    return maintenanceMode.mode === maintenance.mode && maintenanceMode.message === maintenance.message;
  };

  const onSave = async () => {
    try {
      await updateMaintenanceMode(maintenance);
      updateMode(maintenance);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('settings:onUpdateMaintenanceError'), e as AxiosError);
    }
  };

  return (
    <div className={classes.root}>
      <div className={classes.main}>
        <div className={classes.header}>
          <FormControl component="fieldset">
            <RadioGroup className={classes.radioGroup} aria-label="status" name="status1" value={maintenance.mode} onChange={handleChange}>
              <FormControlLabel value={MaintenanceMode.NORMAL} control={<Radio />} label="Normal" />
              <FormControlLabel value={MaintenanceMode.MAINTENANCE_MODE} control={<Radio />} label="Maintenance" />
              <FormControlLabel value={MaintenanceMode.MESSAGE_MODE} control={<Radio />} label="Message" />
            </RadioGroup>
          </FormControl>
        </div>
        {maintenance.mode !== MaintenanceMode.NORMAL && (
        <div className={classes.content}>
          <TextField
            variant="outlined"
            fullWidth
            label="Message"
            id="fullWidth"
            value={maintenance.message !== undefined ? maintenance.message : ''}
            onChange={(event) => setMaintenance({ mode: maintenance.mode, message: event.target.value as string })}
          />
        </div>
        )}
        <div className={classes.footer} style={{ justifyContent: maintenance.mode === MaintenanceMode.NORMAL ? 'flex-start' : 'flex-end' }}>
          <Button variant="contained" onClick={() => setOpenConfirmationModal(true)} color="primary" disabled={isUpdated()}>
            Save
          </Button>
        </div>
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={t('settings:updateMaintenanceModeConfirmation')}
          handleYes={onSave}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      </div>
    </div>
  );
};

export default connector(Maintenance);
