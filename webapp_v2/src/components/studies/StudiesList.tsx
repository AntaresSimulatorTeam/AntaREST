import React, { useEffect, useState } from 'react';
import debug from 'debug';
import { connect, ConnectedProps } from 'react-redux';
import { Box, Grid, Typography, Breadcrumbs, Select, MenuItem, ListItemText, SelectChangeEvent, Popover } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { AxiosError } from 'axios';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import HomeIcon from '@mui/icons-material/Home';
import { GenericInfo, StudyMetadata, SortElement, SortItem, SortStatus } from '../../common/types';
import StudyCard from './StudyCard';
import { scrollbarStyle, STUDIES_HEIGHT_HEADER, STUDIES_LIST_HEADER_HEIGHT } from '../../theme';
import { AppState } from '../../store/reducers';
import { removeStudies } from '../../store/study';
import enqueueErrorSnackbar from '../common/ErrorSnackBar';
import { deleteStudy as callDeleteStudy, copyStudy as callCopyStudy, archiveStudy as callArchiveStudy, unarchiveStudy as callUnarchiveStudy } from '../../services/api/study';

const logError = debug('antares:studieslist:error');

const mapState = (state: AppState) => ({
  scrollPosition: state.study.scrollPosition,
});

const mapDispatch = ({
  removeStudy: (sid: string) => removeStudies([sid]),
});

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
interface OwnProps {
  studies: Array<StudyMetadata>;
  folder: string;
  setFolder: (folder: string) => void;
  favorite: Array<string>;
  onFavoriteClick: (value: GenericInfo) => void;
  sortItem: SortItem;
  setSortItem: (value: SortItem) => void;
}
type PropTypes = PropsFromRedux & OwnProps;

function StudiesList(props: PropTypes) {
  const { studies, folder, sortItem, setFolder, favorite, setSortItem, onFavoriteClick, removeStudy } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [folderList, setFolderList] = useState<Array<string>>([]);
  const [anchorCardMenuEl, setCardMenuAnchorEl] = useState<HTMLButtonElement | null>(null);

  const open = Boolean(anchorCardMenuEl);
  const id = open ? 'simple-popover' : undefined;
  const filterList : Array<GenericInfo> = [
    { id: SortElement.NAME, name: t('studymanager:sortByName') },
    { id: SortElement.DATE, name: t('studymanager:sortByDate') },
  ];

  const archiveStudy = async (study: StudyMetadata) => {
    try {
      await callArchiveStudy(study.id);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:archivefailure', { studyname: study.name }), e as AxiosError);
    }
  };

  const unarchiveStudy = async (study: StudyMetadata) => {
    try {
      await callUnarchiveStudy(study.id);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:unarchivefailure', { studyname: study.name }), e as AxiosError);
    }
  };

  const deleteStudy = async (study: StudyMetadata) => {
    // eslint-disable-next-line no-alert
    try {
      await callDeleteStudy(study.id);
      removeStudy(study.id);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtodeletestudy'), e as AxiosError);
      logError('Failed to delete study', study, e);
    }
  };

  useEffect(() => {
    setFolderList(folder.split('/'));
  }, [folder]);

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
              index === 0 ? (
                <HomeIcon
                  // eslint-disable-next-line react/no-array-index-key
                  key={`${elm}-${index}`}
                  sx={{
                    color: 'text.primary',
                    cursor: 'pointer',
                    '&:hover': {
                      color: 'primary.main',
                    },
                  }}
                  onClick={() => setFolder('root')}
                />
              ) : (
                <Typography
                  // eslint-disable-next-line react/no-array-index-key
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
              )
            ))}
        </Breadcrumbs>
        <Box display="flex" flexDirection="column" justifyContent="center" alignItems="flex-start" boxSizing="border-box">
          <Typography sx={{ mt: 1, p: 0, color: 'rgba(255, 255, 255, 0.7)', fontSize: '12px' }}>{t('studymanager:sortBy')}</Typography>
          <Select
            labelId={`single-checkbox-label-${t('studymanager:sortBy')}`}
            id={`single-checkbox-${t('studymanager:sortBy')}`}
            value={sortItem.element}
            variant="filled"
            onChange={(e: SelectChangeEvent<string>) => setSortItem({ element: e.target.value as SortElement, status: SortStatus.INCREASE })}
            sx={{
              width: '200px',
              height: '50px',
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
        <Grid container spacing={{ xs: 2, md: 3 }} columns={{ xs: 4, sm: 8, md: 12 }} p={2} sx={{ flex: 'none' }}>
          {studies.map((elm) => (
            <Grid item xs={2} sm={4} md={4} key={elm.id}>
              <StudyCard
                study={elm}
                favorite={favorite.includes(elm.id)}
                onFavoriteClick={onFavoriteClick}
                onArchiveClick={archiveStudy}
                onUnarchiveClick={unarchiveStudy}
                onDeleteClick={deleteStudy}
              />
            </Grid>
          ))}
        </Grid>
      </Box>
    </Box>
  );
}

export default connector(StudiesList);
