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
  Button,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import SaveIcon from '@material-ui/icons/Save';
import VisibilityIcon from '@material-ui/icons/Visibility';
import { XpansionSettings } from './types';
import SelectBasic from '../../ui/SelectBasic';

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
        width: '270px',
        marginRight: theme.spacing(2),
        marginBottom: theme.spacing(2),
      },
    },
    select: {
      display: 'flex',
      alignItems: 'center',
      width: '270px',
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

  const ucType = ['expansion_fast', 'expansion_accurate'];
  const master = ['relaxed', 'integer'];
  const solver = ['Cbc', 'Xpress'];
  const cutType = ['yearly', 'weekly', 'average'];

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
          <Box className={classes.select}>
            <SelectBasic name={t('xpansion:ucType')} items={ucType} label="uc_type" value={currentSettings.uc_type} handleChange={handleChange} />
          </Box>
          <Box className={classes.select}>
            <SelectBasic name={t('xpansion:master')} items={master} label="master" value={currentSettings.master} handleChange={handleChange} />
          </Box>
          <TextField type="number" label={t('xpansion:optimalyGap')} variant="filled" value={currentSettings.optimality_gap} onChange={(e) => handleChange('optimality_gap', parseFloat(e.target.value))} />
          <TextField label={t('xpansion:maxIteration')} variant="filled" value={currentSettings.max_iteration || ''} onChange={(e) => handleChange('max_iteration', parseFloat(e.target.value))} />
          <TextField type="number" label={t('xpansion:relaxedOptimalityGap')} variant="filled" value={currentSettings['relaxed-optimality-gap'] || ''} onChange={(e) => handleChange('relaxed-optimality-gap', parseFloat(e.target.value))} />
          <Box className={classes.select}>
            <SelectBasic name={t('xpansion:cutType')} items={cutType} label="cut_type" value={currentSettings.cut_type || ''} handleChange={handleChange} />
          </Box>
          <TextField label={t('xpansion:amplSolver')} variant="filled" value={currentSettings['ampl.solver'] || ''} onChange={(e) => handleChange('ampl.solver', e.target.value)} />
          <TextField type="number" label={t('xpansion:amplPresolve')} variant="filled" value={currentSettings['ampl.presolve'] || ''} onChange={(e) => handleChange('ampl.presolve', parseFloat(e.target.value))} />
          <TextField type="number" label={t('xpansion:amplSolverBoundsFrequency')} variant="filled" value={currentSettings['ampl.solve_bounds_frequency'] || ''} onChange={(e) => handleChange('ampl.solve_bounds_frequency', parseFloat(e.target.value))} />
          <TextField type="number" label={t('xpansion:relativeGap')} variant="filled" value={currentSettings.relative_gap || ''} onChange={(e) => handleChange('relative_gap', parseFloat(e.target.value))} />
          <Box className={classes.select}>
            <SelectBasic name={t('xpansion:solver')} items={solver} label="solver" value={currentSettings.solver || ''} handleChange={handleChange} optional />
          </Box>
        </Box>
      </Box>
      <Box>
        <Typography className={classes.title}>
          {t('xpansion:extra')}
        </Typography>
        <Divider className={classes.divider} />
        <Box className={classes.selectBox}>
          <Box className={classes.select}>
            <SelectBasic name={t('xpansion:yearlyWeight')} items={constraints} label="yearly-weights" value={currentSettings['yearly-weights'] || ''} handleChange={handleChange} optional />
            <VisibilityIcon className={classes.icon} color="primary" onClick={() => currentSettings['yearly-weights'] && onRead(currentSettings['yearly-weights'] || '')} />
          </Box>
          <Box className={classes.select}>
            <SelectBasic name={t('xpansion:additionalConstraints')} items={constraints} label="additional-constraints" value={currentSettings['additional-constraints'] || ''} handleChange={handleChange} optional />
            <VisibilityIcon className={classes.icon} color="primary" onClick={() => currentSettings['additional-constraints'] && onRead(currentSettings['additional-constraints'] || '')} />
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default SettingsForm;
