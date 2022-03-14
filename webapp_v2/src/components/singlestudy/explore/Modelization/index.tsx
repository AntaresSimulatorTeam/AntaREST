/* eslint-disable react-hooks/exhaustive-deps */
import React, { useMemo } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Box } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import debug from 'debug';
import { StudyMetadata } from '../../../../common/types';
import TabWrapper from '../../../common/TabWrapper';

const logError = debug('antares:singlestudy:error');

function Modelization() {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  const tabList = useMemo(() => [{ label: 'Map', path: `/studies/${study?.id}/explore/modelization/map` },
    { label: 'Area', path: `/studies/${study?.id}/explore/modelization/area` },
    { label: 'Links', path: `/studies/${study?.id}/explore/modelization/links` },
    { label: 'Binding contraint', path: `/studies/${study?.id}/explore/modelization/bindingcontraint` },
  ], [study]);

  return (
    <Box width="100%" flexGrow={1} display="flex" flexDirection="column" justifyContent="center" alignItems="center" boxSizing="border-box" overflow="hidden">
      <TabWrapper study={study} tabStyle="withoutBorder" tabList={tabList} />
    </Box>
  );
}

export default Modelization;
