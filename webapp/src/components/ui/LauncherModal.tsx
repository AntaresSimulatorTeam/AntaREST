import React, { useState } from 'react';
import { createStyles, makeStyles, Theme, Button, Paper, FormGroup, FormControlLabel, Checkbox, Typography, FormControl, TextField } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import Modal from '@material-ui/core/Modal';
import Backdrop from '@material-ui/core/Backdrop';
import Fade from '@material-ui/core/Fade';
import { useTranslation } from 'react-i18next';
import { AxiosError } from 'axios';
import clsx from 'clsx';
import enqueueErrorSnackbar from './ErrorSnackBar';
import { LaunchOptions, launchStudy } from '../../services/api/study';
import { StudyMetadata } from '../../common/types';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    overflowY: 'auto',
    boxSizing: 'border-box',
    padding: theme.spacing(2),
  },
  main: {
    backgroundColor: 'white',
    display: 'flex',
    flexFlow: 'column nowrap',
    alignItems: 'center',
    width: '400px',
    height: '450px',
  },
  titlebox: {
    height: '40px',
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    alignItems: 'center',
    backgroundColor: theme.palette.primary.main,
  },
  title: {
    fontWeight: 'bold',
    color: 'white',
    marginLeft: theme.spacing(2),
    overflow: 'hidden',
  },
  content: {
    flex: '1',
    minWidth: '100px',
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    overflow: 'hidden',
    boxSizing: 'border-box',
    padding: theme.spacing(2),
  },
  footer: {
    height: '60px',
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },
  optionTitle: {
    fontSize: '1.2em',
    fontWeight: 'bold',
    marginBottom: theme.spacing(3),
  },
  fieldSection: {
    marginTop: theme.spacing(1),
    width: '100%',
  },
  button: {
    margin: theme.spacing(2),
  },

}));

interface PropTypes {
    open: boolean;
    study?: StudyMetadata;
    close: () => void;
}

const LauncherModal = (props: PropTypes) => {
  const { open, study, close } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [options, setOptions] = useState<LaunchOptions>({});
  const classes = useStyles();

  const launch = async () => {
    if (!study) {
      enqueueSnackbar(t('studymanager:failtorunstudy'), { variant: 'error' });
      return;
    }
    try {
      await launchStudy(study.id, options);
      enqueueSnackbar(t('studymanager:studylaunched', { studyname: study.name }), { variant: 'success' });
      close();
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtorunstudy'), e as AxiosError);
    }
  };

  const handleChange = (field: string, value: number | string | boolean) => {
    setOptions({
      ...options,
      [field]: value,
    });
  };

  const timeLimitParse = (value: any): number => {
    try {
      return parseInt(value, 10) * 3600;
    } catch {
      return 48 * 3600;
    }
  };

  return (
    <Modal
      aria-labelledby="transition-modal-title"
      aria-describedby="transition-modal-description"
      className={classes.root}
      open={open}
      closeAfterTransition
      BackdropComponent={Backdrop}
      BackdropProps={{
        timeout: 500,
      }}
    >
      <Fade in={open}>
        <Paper className={classes.main}>
          <div className={classes.titlebox}>
            <div className={classes.title}>
              {t('singlestudy:runStudy')}
            </div>
          </div>
          <div className={classes.content}>
            <Typography className={classes.optionTitle}>
              Options
            </Typography>
            {/* <Typography>
              {`${t('singlestudy:nbCpu')} : ${options.nb_cpu || 12}`}
            </Typography>
            <FormControl className={clsx(classes.fieldSection)}>
              <Slider
                id="launcher-option-nb-cpu-slider"
                min={1}
                max={12}
                value={options.nb_cpu || 8}
                onChange={(e, value) => handleChange('nb_cpu', value as number)}
                valueLabelDisplay="auto"
                aria-labelledby="continuous-slider"
              />
            </FormControl> */}
            <FormControl className={clsx(classes.fieldSection)}>
              <TextField
                id="launcher-option-time-limit"
                label={t('singlestudy:timeLimit')}
                type="number"
                value={(options.time_limit === undefined ? 172800 : options.time_limit) / 3600}
                onChange={(e) => handleChange('time_limit', timeLimitParse(e.target.value))}
                InputLabelProps={{
                  shrink: true,
                }}
                helperText={t('singlestudy:timeLimitHelper')}
              />
            </FormControl>
            {/* <FormGroup className={clsx(classes.fieldSection)}>
              <FormControlLabel control={<Checkbox checked={!!options.post_processing} onChange={(e, checked) => handleChange('post_processing', checked)} />} label={t('singlestudy:postProcessing')} />
            </FormGroup> */}
            <FormGroup className={clsx(classes.fieldSection)}>
              <FormControlLabel control={<Checkbox checked={!!options.xpansion} onChange={(e, checked) => { handleChange('xpansion', checked); }} />} label={t('singlestudy:xpansionMode')} />
              <FormControlLabel control={<Checkbox checked={!!options.xpansion && !!options.xpansion_r_version} onChange={(e, checked) => handleChange('xpansion_r_version', checked)} />} label={t('singlestudy:useXpansionVersionR')} />
            </FormGroup>
          </div>
          <div className={classes.footer}>
            <Button
              variant="contained"
              className={classes.button}
              color="primary"
              onClick={launch}
            >
              {t('main:launch')}
            </Button>
            <Button
              variant="contained"
              className={classes.button}
              onClick={close}
            >
              {t('main:cancel')}
            </Button>
          </div>
        </Paper>
      </Fade>
    </Modal>
  );
};

LauncherModal.defaultProps = {
  study: undefined,
};

export default LauncherModal;
