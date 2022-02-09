import React, { useEffect } from 'react';
import { Box, Grid } from '@mui/material';
import { StudyMetadata } from '../../common/types';
import StudyCard from './StudyCard';
import { STUDIES_HEIGHT_HEADER, STUDIES_LIST_HEADER_HEIGHT } from '../../theme';

interface PropTypes {
    studies: Array<StudyMetadata>;
}

function StudiesList(props: PropTypes) {
  const { studies } = props;
  useEffect(() => {
    console.log('STUDIES:', studies);
  }, [studies]);
  return (
    <Box
      height={`calc(100vh - ${STUDIES_HEIGHT_HEADER}px)`}
      flex={1}
      display="flex"
      flexDirection="column"
      justifyContent="flex-start"
      alignItems="center"
      boxSizing="border-box"
      sx={{ overflowX: 'hidden', overflowY: 'hidden' }}
    >
      <Box
        width="100%"
        height={`${STUDIES_LIST_HEADER_HEIGHT}`}
        display="flex"
        flexDirection="row"
        justifyContent="flex-end"
        alignItems="center"
        boxSizing="border-box"
      />
      <Box
        width="100%"
        height="100%"
        boxSizing="border-box"
        overflow="auto"
        sx={{ '&::-webkit-scrollbar': {
          width: 7,
        },
        '&::-webkit-scrollbar-track': {
          boxShadow: 'inset 0 0 6px rgba(0, 0, 0, 0.3)',
        },
        '&::-webkit-scrollbar-thumb': {
          backgroundColor: 'secondary.main', // "darkgrey"
          outline: '1px solid slategrey',
        } }}
      >
        <Grid container spacing={{ xs: 2, md: 3 }} columns={{ xs: 4, sm: 8, md: 12 }} p={2}>
          {studies.map((elm) => (
            <Grid item xs={2} sm={4} md={4} key={elm.id}>
              <StudyCard study={elm} />
            </Grid>
          ))}
        </Grid>
      </Box>
    </Box>
  );
}

export default StudiesList;
