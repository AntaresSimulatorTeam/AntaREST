import React from 'react';
import {
  makeStyles,
  createStyles,
  TextField,
  Box,
  Divider,
  Theme,
} from '@material-ui/core';
import { XpansionSettings } from './types';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    fields: {
      display: 'flex',
      justifyContent: 'flex-start',
      alignItems: 'center',
      width: '100%',
      flexWrap: 'wrap',
    },
    divider: {
      marginTop: theme.spacing(1),
      marginBottom: theme.spacing(1),
    },
  }));

interface PropType {
    settings: XpansionSettings;
    updateSettings: (value: XpansionSettings) => void;
}

const SettingsForm = (props: PropType) => {
  const classes = useStyles();
  const { settings, updateSettings } = props;

  return (
    <Box>
      <div>
        Settings
      </div>
      <Divider className={classes.divider} />
      <div className={classes.fields}>
        <TextField label="uc_type" variant="filled" value={settings.uc_type} onBlur={() => updateSettings(settings)} />
        <TextField label="master" variant="filled" value={settings.master} onBlur={() => updateSettings(settings)} />
        <TextField label="optimaly_gap" variant="filled" value={settings.optimaly_gap || ''} onBlur={() => updateSettings(settings)} />
        <TextField label="max_iteration" variant="filled" value={settings.max_iteration || ''} onBlur={() => updateSettings(settings)} />
        <TextField label="yearly_weight" variant="filled" value={settings.yearly_weight || ''} onBlur={() => updateSettings(settings)} />
        <TextField label="additional_constraints" variant="filled" value={settings.additional_constraints || ''} onBlur={() => updateSettings(settings)} />
        <TextField label="relaxed_optimality_gap" variant="filled" value={settings.relaxed_optimality_gap || ''} onBlur={() => updateSettings(settings)} />
        <TextField label="cut_type" variant="filled" value={settings.cut_type || ''} onBlur={() => updateSettings(settings)} />
        <TextField label="ampl_solver" variant="filled" value={settings.ampl_solver || ''} onBlur={() => updateSettings(settings)} />
        <TextField label="ampl_presolve" variant="filled" value={settings.ampl_presolve || ''} onBlur={() => updateSettings(settings)} />
        <TextField label="ampl_solve_bounds_frequency" variant="filled" value={settings.ampl_solve_bounds_frequency || ''} onBlur={() => updateSettings(settings)} />
        <TextField label="relative_gap" variant="filled" value={settings.relative_gap || ''} onBlur={() => updateSettings(settings)} />
        <TextField label="solver" variant="filled" value={settings.solver || ''} onBlur={() => updateSettings(settings)} />
      </div>
    </Box>
  );
};

export default SettingsForm;
