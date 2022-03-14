/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Box, Button, Divider, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import moment from 'moment';
import { AxiosError } from 'axios';
import debug from 'debug';
import { StudyMetadata, VariantTree } from '../../common/types';
import enqueueErrorSnackbar from '../../components/common/ErrorSnackBar';
import { getStudyMetadata } from '../../services/api/study';
import NavHeader from '../../components/singlestudy/NavHeader';
import { getDirectParent, getVariantChildren } from '../../services/api/variant';

const logError = debug('antares:singlestudy:error');

function SingleStudy() {
  const { studyId } = useParams();
  const [t] = useTranslation();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [study, setStudy] = useState<StudyMetadata>();
  const [parent, setParent] = useState<StudyMetadata>();
  const [childrenTree, setChildren] = useState<VariantTree>();

  useEffect(() => {
    const init = async () => {
      if (studyId) {
        try {
          const tmpStudy = await getStudyMetadata(studyId, false);
          if (tmpStudy) {
            const tmpParent = await getDirectParent(tmpStudy.id);
            const childrenTree = await getVariantChildren(tmpStudy.id);
            setStudy(tmpStudy);
            setParent(tmpParent);
            setChildren(childrenTree);
          }
        } catch (e) {
          logError('Failed to fetch study informations', study, e);
        }
      }
    };
    init();
  }, [studyId]);

  return (
    <Box width="100%" height="100%" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="center" boxSizing="border-box" overflow="hidden">
      <NavHeader study={study} parent={parent} childrenTree={childrenTree} />
      <Divider sx={{ width: '98%' }} />
      <Box width="100%" flexGrow={1} display="flex" flexDirection="column" justifyContent="center" alignItems="center" boxSizing="border-box" overflow="hidden">
        <Typography my={2} variant="h5" color="primary">{studyId}</Typography>
        <Button variant="contained" color="primary" onClick={() => navigate(`/studies/${studyId}/explore`)}>
          Open
        </Button>
      </Box>
    </Box>
  );
}

export default SingleStudy;
