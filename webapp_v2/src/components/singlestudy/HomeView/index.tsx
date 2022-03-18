/* eslint-disable react-hooks/exhaustive-deps */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Button, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import debug from 'debug';
import Split from 'react-split';
import { StudyMetadata, VariantTree } from '../../../common/types';
import './Split.css';
import StudyTreeView from './StudyTreeView';
import InformationView from './InformationView';

const logError = debug('antares:singlestudy:error');

interface Props {
    study: StudyMetadata | undefined;
    parents: Array<StudyMetadata>;
    childrenTree: VariantTree | undefined;
}

function HomeView(props: Props) {
  const [t] = useTranslation();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const { study, parents, childrenTree } = props;

  return (
    <Split
      className="split"
      gutterSize={1.5}
      snapOffset={0}
      style={{
        display: 'flex',
        flexDirection: 'row',
      }}
    >
      <Box height="100%" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="flex-start" boxSizing="border-box" overflow="hidden">
        <StudyTreeView study={study} parents={parents} childrenTree={childrenTree} />
      </Box>
      <Box height="100%" display="flex" flexDirection="column" justifyContent="center" alignItems="center" boxSizing="border-box" overflow="hidden">
        <InformationView study={study} />
      </Box>
    </Split>
  );
}

export default HomeView;
