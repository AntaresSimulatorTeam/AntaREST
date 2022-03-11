import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  TextField,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import GenericModal from '../../ui/GenericModal';
import { LinkCreationInfo } from '../MapView/types';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    newCandidate: {
      margin: theme.spacing(2),
      display: 'flex',
      flexDirection: 'column',
      '&>div': {
        margin: theme.spacing(1),
      },
    },
  }));

interface PropType {
    open: boolean;
    links: Array<LinkCreationInfo>;
    onClose: () => void;
    onSave: (name: string, link: string) => void;
}

const CreateCandidateModal = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { open, links, onClose, onSave } = props;
  const [name, setName] = useState<string>('');
  const [link, setLink] = useState<string>('');

  return (
    <GenericModal
      open={open}
      handleClose={onClose}
      handleAction={() => onSave(name, link)}
      title={t('xpansion:newCandidate')}
    >
      <Box className={classes.newCandidate}>
        <TextField
          label={t('main:name')}
          variant="outlined"
          onChange={(event) => setName(event.target.value as string)}
          value={name}
          size="small"
        />
        <FormControl variant="outlined">
          <InputLabel id="link-label">{t('xpansion:link')}</InputLabel>
          <Select
            labelId="link-label"
            id="link-select-outlined"
            value={link}
            onChange={(e) => setLink(e.target.value as string)}
          >
            {links.map((item) => (
              <MenuItem key={`${item.area1} - ${item.area2}`} value={`${item.area1} - ${item.area2}`}>{`${item.area1} - ${item.area2}`}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>
    </GenericModal>
  );
};

export default CreateCandidateModal;
