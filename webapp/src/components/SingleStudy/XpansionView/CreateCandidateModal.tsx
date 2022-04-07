import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  TextField,
  Box,
  Divider,
  ButtonGroup,
  Button,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import GenericModal from '../../ui/GenericModal';
import { LinkCreationInfo } from '../MapView/types';
import SelectBasic from '../../ui/SelectBasic';
import { XpansionCandidate } from './types';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    newCandidate: {
      width: '250px',
      margin: theme.spacing(2),
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'fle-start',
      '& > div': {
        marginBottom: theme.spacing(1),
      },
      '&> svg': {
        marginBottom: theme.spacing(1),
      },
    },
    divider: {
      width: '100%',
      marginTop: theme.spacing(1),
      marginBottom: theme.spacing(2),
    },
    nameField: {
      width: '100%',
    },
    buttongroup: {
      width: '100%',
      display: 'flex',
      justifyContent: 'center',
    },
    button: {
      marginBottom: theme.spacing(1),
    },
    disable: {
      backgroundColor: '#002a5e !important',
      color: 'white !important',
    },
    enable: {
      backgroundColor: 'white',
      color: 'rgba(0, 0, 0, 0.54)',
      border: '1px solid rgba(0, 0, 0, 0.23)',
      '&:hover': {
        backgroundColor: 'rgba(0, 0, 0, 0.12)',
        color: 'rgba(0, 0, 0, 0.26)',
      },
    },
  }));

interface PropType {
    open: boolean;
    links: Array<LinkCreationInfo>;
    onClose: () => void;
    onSave: (candidate: XpansionCandidate) => void;
}

const CreateCandidateModal = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { open, links, onClose, onSave } = props;
  const [candidate, setCandidate] = useState<XpansionCandidate>({
    name: '',
    link: '',
    'annual-cost-per-mw': 0 });
  const [toggleView, setToggleView] = useState<boolean>(true);

  const tabLinks = links.map((item) => `${item.area1} - ${item.area2}`);

  const handleChange = (key: string, value: string | number) => {
    setCandidate({ ...candidate, [key]: value });
  };

  const changeView = () => setToggleView(!toggleView);

  return (
    <GenericModal
      open={open}
      handleClose={onClose}
      handleAction={() => onSave(candidate)}
      title={t('xpansion:newCandidate')}
    >
      <Box className={classes.newCandidate}>
        <TextField
          className={classes.nameField}
          label={t('main:name')}
          variant="outlined"
          onChange={(e) => handleChange('name', e.target.value)}
          value={candidate.name}
          size="small"
        />
        <SelectBasic name={t('xpansion:link')} label="link" items={tabLinks} value={candidate.link} handleChange={handleChange} variant="outlined" />
        <TextField type="number" label={t('xpansion:annualCost')} variant="outlined" value={candidate['annual-cost-per-mw'] || ''} onChange={(e) => handleChange('annual-cost-per-mw', parseFloat(e.target.value))} />
        <Divider className={classes.divider} />
        <Box className={classes.buttongroup}>
          <ButtonGroup className={classes.button} variant="outlined">
            {toggleView ? (
              <Button size="small" variant="outlined" disabled className={classes.disable} color="primary">
                {`${t('xpansion:unitSize')} & ${t('xpansion:maxUnits')}`}
              </Button>
            ) : (
              <Button size="small" variant="outlined" className={classes.enable} color="primary" onClick={changeView}>
                {`${t('xpansion:unitSize')} & ${t('xpansion:maxUnits')}`}
              </Button>
            )}
            {toggleView ? (
              <Button size="small" variant="outlined" className={classes.enable} color="primary" onClick={changeView}>
                {t('xpansion:maxInvestments')}
              </Button>
            ) : (
              <Button size="small" variant="outlined" className={classes.disable} color="primary" disabled>
                {t('xpansion:maxInvestments')}
              </Button>
            )}
          </ButtonGroup>
        </Box>
        {toggleView && (
          <>
            <TextField type="number" label={t('xpansion:unitSize')} variant="outlined" value={candidate['unit-size'] || ''} onChange={(e) => handleChange('unit-size', parseFloat(e.target.value))} />
            <TextField type="number" label={t('xpansion:maxUnits')} variant="outlined" value={candidate['max-units'] || ''} onChange={(e) => handleChange('max-units', parseFloat(e.target.value))} />
          </>
        )}
        {!toggleView && (
        <TextField type="number" label={t('xpansion:maxInvestments')} variant="outlined" value={candidate['max-investment'] || ''} onChange={(e) => handleChange('max-investment', parseFloat(e.target.value))} />
        )}
      </Box>
    </GenericModal>
  );
};

export default CreateCandidateModal;
