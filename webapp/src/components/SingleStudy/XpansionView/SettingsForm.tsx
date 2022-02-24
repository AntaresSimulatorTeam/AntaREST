import React from 'react';
import {
  makeStyles,
  createStyles,
  TextField,
  Box,
  Divider,
  Theme,
  Typography,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import { XpansionSettings } from './types';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    title: {
      color: theme.palette.primary.main,
      fontSize: '1.25rem',
      fontWeight: 400,
      lineHeight: 1.334,
    },
    fields: {
      display: 'flex',
      justifyContent: 'flex-start',
      alignItems: 'center',
      width: '100%',
      flexWrap: 'wrap',
      marginBottom: theme.spacing(2),
      '&> div': {
        marginRight: theme.spacing(2),
        marginBottom: theme.spacing(2),
      },
    },
    divider: {
      marginTop: theme.spacing(1),
      marginBottom: theme.spacing(2),
    },
  }));

interface PropType {
    settings: XpansionSettings;
    updateSettings: (value: XpansionSettings) => void;
}

const SettingsForm = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { settings, updateSettings } = props;

  return (
    <Box>
      <Typography className={classes.title}>
        {t('main:settings')}
      </Typography>
      <Divider className={classes.divider} />
      <div className={classes.fields}>
        <TextField label={t('xpansion:ucType')} variant="filled" value={settings.uc_type} onBlur={() => updateSettings(settings)} />
        <TextField label={t('xpansion:master')} variant="filled" value={settings.master} onBlur={() => updateSettings(settings)} />
        <TextField label={t('xpansion:optimalyGap')} variant="filled" value={settings.optimality_gap} onBlur={() => updateSettings(settings)} />
        <TextField label={t('xpansion:maxIteration')} variant="filled" value={settings.max_iteration || undefined} onBlur={() => updateSettings(settings)} />
        <TextField label={t('xpansion:yearlyWeight')} variant="filled" value={settings.yearly_weight || undefined} onBlur={() => updateSettings(settings)} />
        <TextField label={t('xpansion:additionalConstraints')} variant="filled" value={settings['additional-constraints'] || undefined} onBlur={() => updateSettings(settings)} />
        <TextField label={t('xpansion:relaxedOptimalityGap')} variant="filled" value={settings['relaxed-optimality-gap'] || undefined} onBlur={() => updateSettings(settings)} />
        <TextField label={t('xpansion:cutType')} variant="filled" value={settings.cut_type || undefined} onBlur={() => updateSettings(settings)} />
        <TextField label={t('xpansion:amplSolver')} variant="filled" value={settings['ampl.solver'] || undefined} onBlur={() => updateSettings(settings)} />
        <TextField label={t('xpansion:amplPresolve')} variant="filled" value={settings['ampl.presolve'] || undefined} onBlur={() => updateSettings(settings)} />
        <TextField label={t('xpansion:amplSolverBoundsFrequency')} variant="filled" value={settings['ampl.solve_bounds_frequency'] || undefined} onBlur={() => updateSettings(settings)} />
        <TextField label={t('xpansion:relativeGap')} variant="filled" value={settings.relative_gap || undefined} onBlur={() => updateSettings(settings)} />
        <TextField label={t('xpansion:solver')} variant="filled" value={settings.solver || undefined} onBlur={() => updateSettings(settings)} />
      </div>
    </Box>
  );
};

export default SettingsForm;
