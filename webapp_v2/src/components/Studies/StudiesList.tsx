import React, { useEffect, useState } from 'react';
import { Box, Grid, Typography, Breadcrumbs } from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import HomeIcon from '@mui/icons-material/Home';
import { StudyMetadata } from '../../common/types';
import StudyCard from './StudyCard';
import { scrollbarStyle, STUDIES_HEIGHT_HEADER, STUDIES_LIST_HEADER_HEIGHT } from '../../theme';

interface PropTypes {
    studies: Array<StudyMetadata>;
    folder: string;
    setFolder: (folder: string) => void;
}

function StudiesList(props: PropTypes) {
  const { studies, folder, setFolder } = props

  const [folderList, setFolderList] = useState<Array<string>>([]);

  useEffect(() => {
    setFolderList(folder.split('/'));
  }, [folder])

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
        height={`${STUDIES_LIST_HEADER_HEIGHT}px`}
        px={2}
        display="flex"
        flexDirection="row"
        justifyContent="flex-start"
        alignItems="center"
        boxSizing="border-box"
      >
        <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
          {
            folderList.map((elm, index) => (
              index === 0 ?
              <HomeIcon 
                key={`${elm}-${index}`}
                sx={{
                  color: 'text.primary',
                  cursor: 'pointer',
                  '&:hover': {
                    color: 'primary.main',
                  },
                 }} /> :
              <Typography
                key={`${elm}-${index}`}
                sx={{
                  color: 'text.primary',
                  cursor: 'pointer',
                  '&:hover': {
                    textDecoration: 'underline',
                    color: 'primary.main',
                  },
                }}
                onClick={() => setFolder(folderList.slice(0, index + 1).join('/'))}
              >
                {elm}
              </Typography>
            ))}
        </Breadcrumbs>
      </Box>  
      <Box
        width="100%"
        height="100%"
        boxSizing="border-box"
        overflow="auto"
        sx={scrollbarStyle}
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
