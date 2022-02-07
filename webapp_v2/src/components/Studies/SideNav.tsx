import React from 'react';
import { Box, Typography } from '@mui/material';
import { STUDIES_SIDE_NAV_WIDTH } from '../../theme';

function SideNav() {
  return (
    <Box flex={`0 0 ${STUDIES_SIDE_NAV_WIDTH}px`} height="100%" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="flex-start" boxSizing="border-box"
            p={2} sx={{overflowX: 'hidden', overflowY: 'auto'}}>
        <Typography sx={{ color: 'grey.400' }}>Favorites</Typography>
    </Box>   
  );
}

export default SideNav;
