import React, { useState, useEffect } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  TextField,
  Box,
  Divider,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import DeleteIcon from '@material-ui/icons/Delete';
import ConfirmationModal from '../../ui/ConfirmationModal';
import { XpansionCandidate } from './types';
import { LinkCreationInfo } from '../MapView/types';

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
    deleteIcon: {
      cursor: 'pointer',
      color: theme.palette.error.light,
      '&:hover': {
        color: theme.palette.error.main,
      },
    },
    buttons: {
      position: 'absolute',
      right: '20px',
      bottom: '20px',
    },
    divider: {
      marginTop: theme.spacing(1),
      marginBottom: theme.spacing(2),
    },
    formControl: {
      minWidth: 120,
    },
  }));

interface PropType {
    candidate: XpansionCandidate;
    links: Array<LinkCreationInfo>;
    deleteCandidate: (name: string) => void;
    updateCandidate: (value: XpansionCandidate) => void;
}

const CandidateForm = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { candidate, links, deleteCandidate, updateCandidate } = props;
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);
  const [currentCandidate, setCurrentCandidate] = useState<XpansionCandidate>(candidate);
  const [link, setLink] = useState<string>(candidate.link);

  const handleChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setLink(event.target.value as string);
  };

  useEffect(() => {
    if (candidate) {
      setCurrentCandidate(candidate);
      setLink(candidate.link);
    }
  }, [candidate]);

  console.log(link);

  return (
    <Box>
      <Box>
        <Typography className={classes.title}>
          {t('main:general')}
        </Typography>
        <Divider className={classes.divider} />
        <Box className={classes.fields}>
          <TextField label={t('main:name')} variant="filled" value={candidate.name} onBlur={() => updateCandidate(candidate)} />
          <FormControl variant="filled" className={classes.formControl}>
            <InputLabel id="link-label">{t('xpansion:link')}</InputLabel>
            <Select
              labelId="link-label"
              id="link-select-filled"
              value={link}
              onChange={handleChange}
            >
              {links.map((item) => (
                <MenuItem key={`${item.area1} - ${item.area2}`} value={`${item.area1} - ${item.area2}`}>{`${item.area1} - ${item.area2}`}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      </Box>
      <Box>
        <Typography className={classes.title}>
          {t('main:settings')}
        </Typography>
        <Divider className={classes.divider} />
        <Box className={classes.fields}>
          <TextField label={t('xpansion:annualCost')} variant="filled" value={currentCandidate['annual-cost-per-mw'] || ''} onBlur={() => updateCandidate(candidate)} />
          <TextField label={t('xpansion:unitSize')} variant="filled" value={currentCandidate['unit-size'] || ''} onBlur={() => updateCandidate(candidate)} />
          <TextField label={t('xpansion:maxUnits')} variant="filled" value={currentCandidate['max-units'] || ''} onBlur={() => updateCandidate(candidate)} />
          <TextField label={t('xpansion:maxInvestments')} variant="filled" value={currentCandidate['max-investment'] || ''} onBlur={() => updateCandidate(candidate)} />
          <TextField label={t('xpansion:alreadyICapacity')} variant="filled" value={currentCandidate['already-installed-capacity'] || ''} onBlur={() => updateCandidate(candidate)} />
        </Box>
      </Box>
      <Box>
        <Typography className={classes.title}>
          {t('xpansion:timeSeries')}
        </Typography>
        <Divider className={classes.divider} />
        <Box className={classes.fields}>
          <TextField label={t('xpansion:linkProfile')} variant="filled" value={currentCandidate['link-profile'] || ''} onBlur={() => updateCandidate(candidate)} />
          <TextField label={t('xpansion:alreadyILinkProfile')} variant="filled" value={currentCandidate['already-installed-link-profile'] || ''} onBlur={() => updateCandidate(candidate)} />
        </Box>
      </Box>
      <Box className={classes.buttons}>
        <DeleteIcon className={classes.deleteIcon} onClick={() => setOpenConfirmationModal(true)} />
      </Box>
      {openConfirmationModal && candidate && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message="Êtes-vous sûr de vouloir supprimer ce candidat?"
          handleYes={() => { deleteCandidate(currentCandidate.name); setOpenConfirmationModal(false); }}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
    </Box>
  );
};

export default CandidateForm;
