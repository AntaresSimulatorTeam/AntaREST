import React, { useEffect, useState } from 'react';
import { Box } from '@mui/material';
import { StudyMetadata } from '../../common/types';

interface PropTypes {
    studies: Array<StudyMetadata>;
}

const StudiesList = (props: PropTypes) => {

  return (
    <Box flex={1} height="100%" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="center"
    boxSizing="border-box" sx={{ overflowX: 'hidden',overflowY: 'auto' }}>
        BONJOUR
    </Box>  
  );
}

export default StudiesList;
