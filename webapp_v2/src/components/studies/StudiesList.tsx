import React, { useEffect, useState } from 'react';
import debug from 'debug';
import { connect, ConnectedProps } from 'react-redux';
import { Box, Grid, Typography, Breadcrumbs, Select, MenuItem, ListItemText, SelectChangeEvent, Popover, ListItemIcon } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { AxiosError } from 'axios';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import AutoSizer from 'react-virtualized-auto-sizer';
import HomeIcon from '@mui/icons-material/Home';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import { areEqual, FixedSizeGrid, FixedSizeGridProps, GridChildComponentProps } from 'react-window';
import { GenericInfo, StudyMetadata, SortElement, SortItem, SortStatus } from '../../common/types';
import StudyCard from './StudyCard';
import { scrollbarStyle, STUDIES_HEIGHT_HEADER, STUDIES_LIST_HEADER_HEIGHT } from '../../theme';
import { AppState } from '../../store/reducers';
import { removeStudies } from '../../store/study';
import enqueueErrorSnackbar from '../common/ErrorSnackBar';
import { deleteStudy as callDeleteStudy, copyStudy as callCopyStudy, archiveStudy as callArchiveStudy, unarchiveStudy as callUnarchiveStudy } from '../../services/api/study';
import LauncherModal from './LauncherModal';

const logError = debug('antares:studieslist:error');

const StudyCardCell = React.memo((props: GridChildComponentProps) => {
  const { data, columnIndex, rowIndex, style } = props;
  const { studies, importStudy, onLaunchClick, columnCount, itemWidth, favorite, onFavoriteClick, deleteStudy, archiveStudy, unarchiveStudy } = data;
  const study = studies[columnIndex + rowIndex * columnCount];
  if (study) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', ...style }}>
        <StudyCard
          study={study}
          width={itemWidth}
          favorite={favorite.includes(study.id)}
          onLaunchClick={() => onLaunchClick(study)}
          onFavoriteClick={onFavoriteClick}
          onImportStudy={importStudy}
          onArchiveClick={archiveStudy}
          onUnarchiveClick={unarchiveStudy}
          onDeleteClick={deleteStudy}
        />
      </div>
    );
  }
  return <div />;
}, areEqual);

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
  const [openLaunncherModal, setOpenLauncherModal] = useState<boolean>(false);
  const [currentLaunchStudy, setCurrentLaunchStudy] = useState<StudyMetadata>();
  const [anchorCardMenuEl, setCardMenuAnchorEl] = useState<HTMLButtonElement | null>(null);

  const open = Boolean(anchorCardMenuEl);
  const id = open ? 'simple-popover' : undefined;
  const filterList : Array<SortItem & { name: string }> = [
    { element: SortElement.NAME, name: t('studymanager:sortByName'), status: SortStatus.INCREASE },
    { element: SortElement.NAME, name: t('studymanager:sortByName'), status: SortStatus.DECREASE },
    { element: SortElement.DATE, name: t('studymanager:sortByDate'), status: SortStatus.INCREASE },
    { element: SortElement.DATE, name: t('studymanager:sortByDate'), status: SortStatus.DECREASE },
  ];

  const importStudy = async (study: StudyMetadata, withOutputs: boolean) => {
    try {
      await callCopyStudy(study.id, `${study.name} (${t('main:copy')})`, withOutputs);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtocopystudy'), e as AxiosError);
      logError('Failed to copy/import study', study, e);
    }
  };

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

  const getSortItem = (element: string) : SortItem => {
    const tab = element.split('-');
    if (tab.length === 2) {
      return {
        element: tab[0] as SortElement,
        status: tab[1] as SortStatus,
      };
    }
    return {
      element: SortElement.NAME,
      status: SortStatus.INCREASE,
    };
  };

  const onLaunchClick = (study: StudyMetadata) : void => {
    setCurrentLaunchStudy(study);
    setOpenLauncherModal(true);
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
        <Box display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center" boxSizing="border-box">
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
          <Typography mx={2} color="primary">
            (
            {`${studies.length} ${t('studymanager:studies').toLowerCase()}`}
            )
          </Typography>
        </Box>
        <Box display="flex" flexDirection="column" justifyContent="center" alignItems="flex-start" boxSizing="border-box">
          <Typography sx={{ mt: 1, p: 0, color: 'rgba(255, 255, 255, 0.7)', fontSize: '12px' }}>{t('studymanager:sortBy')}</Typography>
          <Select
            labelId={`single-checkbox-label-${t('studymanager:sortBy')}`}
            id={`single-checkbox-${t('studymanager:sortBy')}`}
            value={`${sortItem.element}-${sortItem.status}`}
            variant="filled"
            onChange={(e: SelectChangeEvent<string>) => setSortItem(getSortItem(e.target.value as string))}
            sx={{
              width: '230px',
              height: '50px',
              '.MuiSelect-select': {
                display: 'flex',
                flexFlow: 'row nowrap',
                justifyContent: 'center',
                alignItems: 'center',
              },
              background: 'rgba(255, 255, 255, 0)',
              borderRadius: '4px 4px 0px 0px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.42)',
              '.MuiSelect-icon': {
                backgroundColor: '#222333',
              },
            }}
          >
            {filterList.map(({ element, name, status }) => {
              const value = `${element}-${status}`;
              return (
                <MenuItem
                  key={value}
                  value={value}
                  sx={{
                    display: 'flex',
                    flexFlow: 'row nowrap',
                    justifyContent: 'center',
                    alignItems: 'center' }}
                >
                  <ListItemIcon sx={{ minWidth: '30px' }}>
                    {status === SortStatus.INCREASE ? <ArrowUpwardIcon /> : <ArrowDownwardIcon />}
                  </ListItemIcon>
                  <ListItemText primary={name} />
                </MenuItem>
              );
            })}
          </Select>
        </Box>
      </Box>
      <Box
        width="100%"
        height="100%"
        boxSizing="border-box"
        sx={{ overflowX: 'hidden', overflowY: 'auto', ...scrollbarStyle }}
      >
        <AutoSizer>
          { ({ height, width }) => {
            const paddedWidth = width - 20;
            const baseColumnCount = Math.floor(paddedWidth / 400);
            const itemWidth = (paddedWidth / Math.round(paddedWidth / 400));
            const columnCount = Math.floor(paddedWidth / itemWidth);
            return (
              <FixedSizeGrid
                columnCount={columnCount}
                columnWidth={itemWidth}
                height={height}
                rowCount={Math.ceil(studies.length / columnCount)}
                rowHeight={210}
                width={width}
                itemData={{ studies, importStudy, onLaunchClick, columnCount, itemWidth, favorite, onFavoriteClick, deleteStudy, archiveStudy, unarchiveStudy }}
              >
                {StudyCardCell}
              </FixedSizeGrid>
            );
          }
        }
        </AutoSizer>
      </Box>
      {openLaunncherModal && <LauncherModal open={openLaunncherModal} study={currentLaunchStudy} onClose={() => setOpenLauncherModal(false)} />}
    </Box>
  );
}

export default connector(StudiesList);
