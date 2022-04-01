/* eslint-disable react-hooks/exhaustive-deps */
import React from 'react';
import { useNavigate, useParams, Outlet } from 'react-router-dom';
import { Box, Button, Paper, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import debug from 'debug';
import { StudyMetadata } from '../../../../common/types';

const logError = debug('antares:singlestudy:error');

interface Props {
    study: StudyMetadata | undefined;
}

function InformationView(props: Props) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { study } = props;

  return (
    <Paper
      sx={{
        width: '80%',
        height: '80%',
      }}
    />
  );
}

export default InformationView;
