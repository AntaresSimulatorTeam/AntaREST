/* eslint-disable @typescript-eslint/camelcase */
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
  Button,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import SaveIcon from '@material-ui/icons/Save';
import VisibilityIcon from '@material-ui/icons/Visibility';
import { XpansionSettings } from './types';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'flex-end',
    },
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
    select: {
      display: 'flex',
      alignItems: 'center',
    },
    selectBox: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'flex-start',
      width: '100%',
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
    icon: {
      marginLeft: theme.spacing(1),
      marginRight: theme.spacing(1),
      '&:hover': {
        color: theme.palette.secondary.main,
        cursor: 'pointer',
      },
    },
    saveButton: {
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'space-between',
      alignItems: 'center',
      height: '30px',
      marginBottom: theme.spacing(1),
    },
    buttonElement: {
      margin: theme.spacing(0.2),
    },
  }));

interface PropType {
    settings: XpansionSettings;
    constraints: Array<string>;
    updateSettings: (value: XpansionSettings) => Promise<void>;
    onRead: (filename: string) => Promise<void>;
}

const SettingsForm = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { settings, constraints, updateSettings, onRead } = props;
  const [currentSettings, setCurrentSettings] = useState<XpansionSettings>(settings);
  const [saveAllowed, setSaveAllowed] = useState<boolean>(false);

  const handleChange = (key: string, value: string | number) => {
    setSaveAllowed(true);
    setCurrentSettings({ ...currentSettings, [key]: value });
  };

  useEffect(() => {
    if (settings) {
      setCurrentSettings(settings);
      setSaveAllowed(false);
    }
  }, [settings]);

  return (
    <Box>
      <Box>
        <Box className={classes.header}>
          <Typography className={classes.title}>
            {t('main:settings')}
          </Typography>
          <Button
            variant="outlined"
            color="primary"
            className={classes.saveButton}
            style={{ border: '2px solid' }}
            onClick={() => { updateSettings(currentSettings); setSaveAllowed(false); }}
            disabled={!saveAllowed}
          >
            <SaveIcon className={classes.buttonElement} style={{ width: '16px', height: '16px' }} />
            <Typography className={classes.buttonElement} style={{ fontSize: '12px' }}>{t('main:save')}</Typography>
          </Button>
        </Box>
        <Divider className={classes.divider} />
        <Box className={classes.fields}>
          <TextField label={t('xpansion:ucType')} variant="filled" value={currentSettings.uc_type} onChange={(e) => handleChange('uc_type', e.target.value)} />
          <TextField label={t('xpansion:master')} variant="filled" value={currentSettings.master} onChange={(e) => handleChange('master', e.target.value)} />
          <TextField type="number" label={t('xpansion:optimalyGap')} variant="filled" value={currentSettings.optimality_gap} onChange={(e) => handleChange('optimality_gap', parseFloat(e.target.value))} />
          <TextField label={t('xpansion:maxIteration')} variant="filled" value={currentSettings.max_iteration || ''} onChange={(e) => handleChange('max_iteration', parseFloat(e.target.value))} />
          <TextField type="number" label={t('xpansion:relaxedOptimalityGap')} variant="filled" value={currentSettings['relaxed-optimality-gap'] || ''} onChange={(e) => handleChange('relaxed-optimality-gap', parseFloat(e.target.value))} />
          <TextField label={t('xpansion:cutType')} variant="filled" value={currentSettings.cut_type || ''} onChange={(e) => handleChange('cut_type', e.target.value)} />
          <TextField label={t('xpansion:amplSolver')} variant="filled" value={currentSettings['ampl.solver'] || ''} onChange={(e) => handleChange('ampl.solver', e.target.value)} />
          <TextField type="number" label={t('xpansion:amplPresolve')} variant="filled" value={currentSettings['ampl.presolve'] || ''} onChange={(e) => handleChange('ampl.presolve', parseFloat(e.target.value))} />
          <TextField type="number" label={t('xpansion:amplSolverBoundsFrequency')} variant="filled" value={currentSettings['ampl.solve_bounds_frequency'] || ''} onChange={(e) => handleChange('ampl.solve_bounds_frequency', parseFloat(e.target.value))} />
          <TextField type="number" label={t('xpansion:relativeGap')} variant="filled" value={currentSettings.relative_gap || ''} onChange={(e) => handleChange('relative_gap', parseFloat(e.target.value))} />
          <TextField label={t('xpansion:solver')} variant="filled" value={currentSettings.solver || ''} onChange={(e) => handleChange('solver', e.target.value)} />
        </Box>
      </Box>
      <Box>
        <Typography className={classes.title}>
          {t('xpansion:extra')}
        </Typography>
        <Divider className={classes.divider} />
        <Box className={classes.selectBox}>
          <Box className={classes.select}>
            <FormControl variant="filled" className={classes.formControl}>
              <InputLabel id="link-label">{t('xpansion:yearlyWeight')}</InputLabel>
              <Select
                labelId="yearly-weight-label"
                id="yearly-weight-select-filled"
                value={currentSettings['yearly-weights'] || ''}
                onChange={(e) => handleChange('yearly-weights', e.target.value as string)}
              >
                <MenuItem value="" key="None">{t('main:none')}</MenuItem>
                {constraints.map((item) => (
                  <MenuItem value={item} key={item}>{item}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <VisibilityIcon className={classes.icon} color="primary" onClick={() => currentSettings['yearly-weights'] && onRead(currentSettings['yearly-weights'] || '')} />
          </Box>
          <Box className={classes.select}>
            <FormControl variant="filled" className={classes.formControl}>
              <InputLabel id="link-label">{t('xpansion:additionalConstraints')}</InputLabel>
              <Select
                labelId="additional-constraints-label"
                id="additional-constraints-select-filled"
                value={currentSettings['additional-constraints'] || ''}
                onChange={(e) => handleChange('additional-constraints', e.target.value as string)}
              >
                <MenuItem value="" key="None">{t('main:none')}</MenuItem>
                {constraints.map((item) => (
                  <MenuItem value={item} key={item}>{item}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <VisibilityIcon className={classes.icon} color="primary" onClick={() => currentSettings['additional-constraints'] && onRead(currentSettings['additional-constraints'] || '')} />
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default SettingsForm;
