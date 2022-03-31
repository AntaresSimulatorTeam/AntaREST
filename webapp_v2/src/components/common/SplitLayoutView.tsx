import React, { ReactNode } from 'react';
import {
  Divider,
  Box,
} from '@mui/material';

interface Props {
  left: ReactNode;
  right: ReactNode;
}

function SplitLayoutView(props: Props) {
  const { left, right } = props;

  return (
    <Box width="100%" display="flex" justifyContent="space-evenly" alignItems="center" overflow="hidden" flexGrow="1">
      <Box width="20%" height="100%" position="relative">
        {left}
      </Box>
      <Divider sx={{ height: '96%' }} orientation="vertical" variant="middle" />
      <Box width="80%" height="100%" display="flex" justifyContent="center" alignItems="flex-start" position="relative" overflow="hidden">
        {right}
      </Box>
    </Box>
  );
}

export default SplitLayoutView;
