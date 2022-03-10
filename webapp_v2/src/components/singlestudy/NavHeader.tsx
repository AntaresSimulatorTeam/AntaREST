/* eslint-disable react-hooks/exhaustive-deps */
import React, { PropsWithChildren, useEffect, useState } from 'react';
import { BrowserRouter as Router, Navigate, Route, Routes, useNavigate, useParams } from 'react-router-dom';
import { Box, Button, Divider, Typography } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { connect, ConnectedProps } from 'react-redux';
import moment from 'moment';
import { StudyMetadata } from '../../common/types';

interface Props {
    study: StudyMetadata;
    backLabel: string;
    goBack: () => void;
}

function NavHeader(props: PropsWithChildren<Props>) {
  const { study, backLabel, goBack, children } = props;
  const [t] = useTranslation();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();

  return (
    <Box width="100%" height="100px" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="center" boxSizing="border-box" overflow="hidden">
      <Box width="100%" display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center" boxSizing="border-box">
        <ArrowBackIcon color="secondary" />
        <Button variant="text" color="secondary">{backLabel}</Button>
      </Box>
      <Box width="100%" display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center" boxSizing="border-box" />
      <Box width="100%" display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center" boxSizing="border-box" />
    </Box>
  );
}

export default NavHeader;
