import React from 'react';
import { styled, useTheme } from '@mui/material/styles';
import Header from '../../components/Studies/Header';
import { Box, Divider, Typography } from '@mui/material';
import SideNav from '../../components/Studies/SideNav';
import StudiesList from '../../components/Studies/StudiesList';

function Studies() {
  const theme = useTheme();
  return (
    <Box width="100%" height="100%" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="center" boxSizing="border-box" bgcolor="primary.main">
        <Header />
        <Divider style={{ width: '98%', height: '1px', background: theme.palette.grey[800] }}/>
        <Box flex={1} width="100%" display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center" boxSizing="border-box">
          <SideNav />
          <Divider style={{ width: '1px', height: '98%', background: theme.palette.grey[800] }}/>
          <StudiesList />
        </Box>
     </Box>   
  );
}

export default Studies;
