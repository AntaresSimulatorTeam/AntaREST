import React, { useState, useEffect } from 'react';
import {
  makeStyles,
  createStyles,
  TextField,
  Box,
  Divider,
  Theme,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
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
    formControl: {
      minWidth: '210px',
    },
  }));

interface PropType {
    settings: XpansionSettings;
    constraints: Array<string>;
    updateSettings: (value: XpansionSettings) => void;
}

const SettingsForm = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { settings, constraints, updateSettings } = props;
  const [currentSettings, setCurrentSettings] = useState<XpansionSettings>(settings);
  const [constraint, setConstraint] = useState<string>(settings['additional-constraints'] || '');
  const [yearlyWeight, setYearlyWeight] = useState<string>(settings.yearly_weight || '');

  const handleConstraintChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setConstraint(event.target.value as string);
  };

  const handleWeightChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setYearlyWeight(event.target.value as string);
  };

  useEffect(() => {
    if (settings) {
      setCurrentSettings(settings);
      setConstraint(settings['additional-constraints'] || '');
      setYearlyWeight(settings.yearly_weight || '');
    }
  }, [settings]);

  return (
    <Box>
      <Box>
        <Typography className={classes.title}>
          {t('main:settings')}
        </Typography>
        <Divider className={classes.divider} />
        <Box className={classes.fields}>
          <TextField label={t('xpansion:ucType')} variant="filled" value={currentSettings.uc_type} onBlur={() => updateSettings(settings)} />
          <TextField label={t('xpansion:master')} variant="filled" value={currentSettings.master} onBlur={() => updateSettings(settings)} />
          <TextField label={t('xpansion:optimalyGap')} variant="filled" value={currentSettings.optimality_gap} onBlur={() => updateSettings(settings)} />
          <TextField label={t('xpansion:maxIteration')} variant="filled" value={currentSettings.max_iteration || undefined} onBlur={() => updateSettings(settings)} />
          <TextField label={t('xpansion:relaxedOptimalityGap')} variant="filled" value={currentSettings['relaxed-optimality-gap'] || undefined} onBlur={() => updateSettings(settings)} />
          <TextField label={t('xpansion:cutType')} variant="filled" value={currentSettings.cut_type || undefined} onBlur={() => updateSettings(settings)} />
          <TextField label={t('xpansion:amplSolver')} variant="filled" value={currentSettings['ampl.solver'] || undefined} onBlur={() => updateSettings(settings)} />
          <TextField label={t('xpansion:amplPresolve')} variant="filled" value={currentSettings['ampl.presolve'] || undefined} onBlur={() => updateSettings(settings)} />
          <TextField label={t('xpansion:amplSolverBoundsFrequency')} variant="filled" value={currentSettings['ampl.solve_bounds_frequency'] || undefined} onBlur={() => updateSettings(settings)} />
          <TextField label={t('xpansion:relativeGap')} variant="filled" value={currentSettings.relative_gap || undefined} onBlur={() => updateSettings(settings)} />
          <TextField label={t('xpansion:solver')} variant="filled" value={currentSettings.solver || undefined} onBlur={() => updateSettings(settings)} />
        </Box>
      </Box>
      <Box>
        <Typography className={classes.title}>
          Extra
        </Typography>
        <Divider className={classes.divider} />
        <Box className={classes.fields}>
          <FormControl variant="filled" className={classes.formControl}>
            <InputLabel id="link-label">{t('xpansion:yearlyWeight')}</InputLabel>
            <Select
              labelId="yearly-weight-label"
              id="yearly-weight-select-filled"
              value={yearlyWeight || ''}
              onChange={handleWeightChange}
            >
              {constraints.map((item) => (
                <MenuItem value={item} key={item}>{item}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl variant="filled" className={classes.formControl}>
            <InputLabel id="link-label">{t('xpansion:additionalConstraints')}</InputLabel>
            <Select
              labelId="additional-constraints-label"
              id="additional-constraints-select-filled"
              value={constraint || ''}
              onChange={handleConstraintChange}
            >
              {constraints.map((item) => (
                <MenuItem value={item} key={item}>{item}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      </Box>
    </Box>
  );
};

export default SettingsForm;
