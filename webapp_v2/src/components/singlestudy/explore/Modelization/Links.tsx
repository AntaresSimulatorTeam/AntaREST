/* eslint-disable react-hooks/exhaustive-deps */
import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { Box, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import debug from 'debug';
import { StudyMetadata } from '../../../../common/types';

const logError = debug('antares:singlestudy:modelization:links:error');

function Links() {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  return (
    <Box width="100%" flexGrow={1} display="flex" flexDirection="column" justifyContent="center" alignItems="center" boxSizing="border-box" overflow="hidden">
      <Typography my={2} variant="h5" color="primary">
        {' '}
        Links:
        {' '}
        <br />
        {' '}
        {study?.id}
      </Typography>
    </Box>
  );
}

export default Links;
