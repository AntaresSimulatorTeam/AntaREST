import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  Typography,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import XpansionPropsView from './XpansionPropsView';
import { StudyMetadata } from '../../../common/types';
import SplitLayoutView from '../../ui/SplitLayoutView';
import CreateCandidateModal from './CreateCandidateModal';
import mockdata from './mockdata.json';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      color: theme.palette.primary.main,
    },
  }));

interface Props {
    study: StudyMetadata;
}

const XpansionView = (props: Props) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { study } = props;
  const [openModal, setOpenModal] = useState<boolean>(false);

  const onSave = () => {
    setOpenModal(false);
  };

  const onClose = () => setOpenModal(false);

  return (
    <>
      <SplitLayoutView
        title={t('singlestudy:xpansion')}
        left={
          <XpansionPropsView candidateList={mockdata} onAdd={() => setOpenModal(true)} />
        }
        right={
          <Typography className={classes.root}>{study.name}</Typography>
        }
      />
      {openModal && (
        <CreateCandidateModal
          open={openModal}
          onClose={onClose}
          onSave={onSave}
        />
      )}
    </>
  );
};

export default XpansionView;
