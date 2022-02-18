import React, { useEffect, useState } from 'react';
import { Box, Grid, Typography, Breadcrumbs, Select, MenuItem, ListItemText, SelectChangeEvent } from '@mui/material';
import { useTranslation } from 'react-i18next';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import HomeIcon from '@mui/icons-material/Home';
import { GenericInfo, StudyMetadata, SortElement, SortItem, SortStatus } from '../../common/types';
import StudyCard from './StudyCard';
import { scrollbarStyle, STUDIES_HEIGHT_HEADER, STUDIES_LIST_HEADER_HEIGHT } from '../../theme';

interface PropTypes {
    studies: Array<StudyMetadata>;
    folder: string;
    setFolder: (folder: string) => void;
    favorite: Array<string>;
    onFavoriteClick: (value: GenericInfo) => void;
    sortItem: SortItem;
    setSortItem: (value: SortItem) => void;
}

function StudiesList(props: PropTypes) {
  const { studies, folder, sortItem, setFolder, favorite, setSortItem, onFavoriteClick } = props;
  const [t] = useTranslation();
  const [folderList, setFolderList] = useState<Array<string>>([]);
  const filterList : Array<GenericInfo> = [
    { id: SortElement.NAME, name: t('studymanager:sortByName') },
    { id: SortElement.DATE, name: t('studymanager:sortByDate')  },
  ];

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
        justifyContent="space-between"
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
        <Box display="flex" flexDirection="column" justifyContent="center" alignItems="flex-start" boxSizing="border-box">
          <Typography sx={{ mt: 1, p: 0, color: 'rgba(255, 255, 255, 0.7)', fontSize: '12px' }} >{t('studymanager:sortBy')}</Typography>
          <Select
            labelId={`single-checkbox-label-${t('studymanager:sortBy')}`}
            id={`single-checkbox-${t('studymanager:sortBy')}`}
            value={sortItem.element}
            variant="filled"
            onChange={(e: SelectChangeEvent<string>) => setSortItem({element: e.target.value as SortElement, status: SortStatus.INCREASE})}
            sx={{
              height: '40px', 
              background: 'rgba(255, 255, 255, 0)',
              borderRadius: '4px 4px 0px 0px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.42)',
              '.MuiSelect-icon': {
                backgroundColor: '#222333',
              },
            }}
          >
            {filterList.map(({ id, name }) => (
              <MenuItem key={id} value={id}>
                <ListItemText primary={name} />
              </MenuItem>
            ))}
        </Select>
        </Box>
      </Box>  
      <Box
        width="100%"
        height="100%"
        boxSizing="border-box"
        sx={{ overflowX: 'hidden', overflowY: 'auto', ...scrollbarStyle }}
      >
        <Grid container spacing={{ xs: 2, md: 3 }} columns={{ xs: 4, sm: 8, md: 12 }} p={2}>
          {studies.map((elm) => (
            <Grid item xs={2} sm={4} md={4} key={elm.id}>
              <StudyCard study={elm} favorite={favorite.includes(elm.id)} onFavoriteClick={onFavoriteClick} />
            </Grid>
          ))}
        </Grid>
      </Box>
    </Box>
  );
}

export default StudiesList;
