import React from 'react';
import { styled, useTheme } from '@mui/material/styles';
import Header from './Header';
import { Divider, Typography } from '@mui/material';

const Root = styled('div')(({ theme }) => ({
  width: '100%',
  height: '100%',
  display: 'flex',
  flexFlow: 'column nowrap',
  justifyContent: 'flex-start',
  alignItems: 'center',
  boxSizing: 'border-box',
  backgroundColor: theme.palette.primary.main,
}));

function Studies() {
  const theme = useTheme();
  return (
    <Root>
        <Header />
        <Divider style={{ width: '98%', height: '1px', background: theme.palette.grey[800] }}/>
        <div style={{
          flex: 1,
          width: '100%',
          display: 'flex',
          flexFlow: 'row nowrap',
          justifyContent: 'flex-start',
          alignItems: 'center',
          boxSizing: 'border-box',          
        }}>
        <div style={{
          flex: '0 0 200px',
          height: '100%',
          display: 'flex',
          flexFlow: 'column nowrap',
          justifyContent: 'flex-start',
          alignItems: 'flex-start',
          boxSizing: 'border-box',
          overflowX: 'hidden',
          overflowY: 'auto',
          padding: theme.spacing(2,2),          
        }}>
          <Typography sx={{ color: theme.palette.grey[400] }}>Favorites</Typography>
        </div>
        <Divider style={{ width: '1px', height: '98%', background: theme.palette.grey[800] }}/>
        <div style={{
          flex: 1,
          height: '100%',
          display: 'flex',
          flexFlow: 'column nowrap',
          justifyContent: 'flex-start',
          alignItems: 'center',
          boxSizing: 'border-box',
          overflowX: 'hidden',
          overflowY: 'auto',        
        }}>

        </div>
        </div>
     </Root>   
  );
}

export default Studies;
