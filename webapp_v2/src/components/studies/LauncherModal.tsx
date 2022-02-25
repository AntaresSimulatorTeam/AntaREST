import React, { useState } from 'react';
import { Box, Checkbox, FormControl, FormControlLabel, FormGroup, TextField, Typography, useTheme } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { AxiosError } from 'axios';
import BasicModal from '../common/BasicModal';
import { StudyMetadata } from '../../common/types';
import { LaunchOptions, launchStudy } from '../../services/api/study';
import enqueueErrorSnackbar from '../common/ErrorSnackBar';

interface Props {
open: boolean;
study?: StudyMetadata;
onClose: () => void;
}

function LauncherModal(props: Props) {
  const { study, open, onClose } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const theme = useTheme();
  const [options, setOptions] = useState<LaunchOptions>({});

  const launch = async () => {
    if (!study) {
      enqueueSnackbar(t('studymanager:failtorunstudy'), { variant: 'error' });
      return;
    }
    try {
      await launchStudy(study.id, options);
      enqueueSnackbar(t('studymanager:studylaunched', { studyname: study.name }), { variant: 'success' });
      onClose();
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtorunstudy'), e as AxiosError);
    }
  };

  const handleChange = (field: string, value: number | string | boolean) => {
    const val = field === 'adequacy_patch' ? {} : value;
    setOptions({
      ...options,
      [field]: val,
    });
  };

  const timeLimitParse = (value: string): number => {
    try {
      return parseInt(value, 10) * 3600;
    } catch {
      return 48 * 3600;
    }
  };

  return (
    <BasicModal
      title={t('singlestudy:runStudy')}
      open={open}
      onClose={onClose}
      closeButtonLabel={t('main:cancelButton')}
      actionButtonLabel={t('main:launch')}
      onActionButtonClick={launch}
      rootStyle={{ width: '600px', height: '500px', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', alignItems: 'center', boxSizing: 'border-box' }}
    >
      <Box minWidth="100px" width="100%" height="100%" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="flex-start" p={2} boxSizing="border-box" overflow="hidden">
        <Typography sx={{
          fontSize: '1.2em',
          fontWeight: 'bold',
          mb: 3,
        }}
        >
          Options
        </Typography>
        <FormControl sx={{
          mt: 1,
          width: '100%',
        }}
        >
          <TextField
            id="launcher-option-time-limit"
            label={t('singlestudy:timeLimit')}
            type="number"
            value={(options.time_limit === undefined ? 172800 : options.time_limit) / 3600}
            onChange={(e) => handleChange('time_limit', timeLimitParse(e.target.value))}
            InputProps={{
              sx: {
                '.MuiOutlinedInput-root': {
                  '&.MuiOutlinedInput-notchedOutline': {
                    borderColor: `${theme.palette.primary.main} !important`,
                  },
                },
                '.Mui-focused': {
                  // borderColor: `${theme.palette.primary.main} !important`
                },
                '.MuiOutlinedInput-notchedOutline': {
                  borderWidth: '1px',
                  borderColor: `${theme.palette.text.secondary} !important`,
                },
              } }}
            InputLabelProps={{
              shrink: true,
              sx: {
                '.MuiInputLabel-root': {
                  color: theme.palette.text.secondary,
                },
                '.Mui-focused': {
                },
              },
            }}
            helperText={t('singlestudy:timeLimitHelper')}
          />
        </FormControl>
        <FormGroup sx={{
          mt: 1,
          width: '100%',
        }}
        >
          <FormControlLabel control={<Checkbox checked={!!options.xpansion} onChange={(e, checked) => { handleChange('xpansion', checked); }} />} label={t('singlestudy:xpansionMode') as string} />
          <FormControlLabel control={<Checkbox checked={!!options.xpansion && !!options.xpansion_r_version} onChange={(e, checked) => handleChange('xpansion_r_version', checked)} />} label={t('singlestudy:useXpansionVersionR') as string} />
          <FormControlLabel control={<Checkbox checked={!!options.adequacy_patch} onChange={(e, checked) => handleChange('adequacy_patch', checked)} />} label="Mode adequacy" />
        </FormGroup>
      </Box>
    </BasicModal>
  );
}

LauncherModal.defaultProps = {
  study: undefined,
};

export default LauncherModal;
