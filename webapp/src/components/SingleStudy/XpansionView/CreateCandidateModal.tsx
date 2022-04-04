import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  TextField,
  Box,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import GenericModal from '../../ui/GenericModal';
import { LinkCreationInfo } from '../MapView/types';
import SelectBasic from '../../ui/SelectBasic';

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

  const tabLinks = links.map((item) => `${item.area1} - ${item.area2}`);

  const handleChange = (key: string, value: string | number) => {
    setLink(value as string);
  };

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
        <SelectBasic name={t('xpansion:link')} label="link" items={tabLinks} value={link} handleChange={handleChange} variant="outlined" />
      </Box>
    </GenericModal>
  );
};

export default CreateCandidateModal;
