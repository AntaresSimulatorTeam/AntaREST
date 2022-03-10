/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Navigate, Route, Routes, useNavigate, useParams } from 'react-router-dom';
import { Box, Button, Divider, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { connect, ConnectedProps } from 'react-redux';
import moment from 'moment';
import { AxiosError } from 'axios';
import debug from 'debug';
import { StudyMetadata } from '../../common/types';
import enqueueErrorSnackbar from '../../components/common/ErrorSnackBar';
import { getStudyMetadata } from '../../services/api/study';

const logErr = debug('antares:studies:error');

function SingleStudy() {
  const { studyId } = useParams();
  const [t] = useTranslation();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [study, setStudy] = useState<StudyMetadata>();

  useEffect(() => {
    const init = async () => {
      if (studyId) {
        try {
          const tmpStudy = await getStudyMetadata(studyId);
          setStudy(study);
        } catch (e) {
          console.log(e);
        }
      }
    };
  }, [studyId]);

  return (
    <Box width="100%" height="100%" display="flex" flexDirection="column" justifyContent="center" alignItems="center" boxSizing="border-box" overflow="hidden">
      <Typography my={2} variant="h5" color="primary">{studyId}</Typography>
      <Button variant="contained" color="primary" onClick={() => navigate(`/studies/${studyId}/explore`)}>
        Open
      </Button>
    </Box>
  );
}

export default SingleStudy;
