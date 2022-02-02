import React, { useEffect, useState } from 'react';
import { Box, Grid } from '@mui/material';
import { StudyMetadata } from '../../common/types';
import StudyCard from './StudyCard';

interface PropTypes {
    studies: Array<StudyMetadata>;
}

const StudiesList = (props: PropTypes) => {
  const { studies } = props;
  return (
    <Box flex={1} height="100%" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="center"
    boxSizing="border-box" bgcolor='red' sx={{ overflowX: 'hidden',overflowY: 'auto' }}>
        <Grid container spacing={{ xs: 2, md: 3 }} columns={{ xs: 4, sm: 8, md: 12 }} sx={{ w: '100%', h: '100%', bgColor: 'primary.light'}}>
          {studies.map((elm, index) => (
            <Grid item xs={2} sm={4} md={4} key={elm.id}>
              <StudyCard />
            </Grid>
          ))}
        </Grid>
    </Box>  
  );
}

export default StudiesList;
