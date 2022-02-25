import React, { useEffect, useState } from 'react';
import debug from 'debug';
import { connect, ConnectedProps } from 'react-redux';
import { areEqual, FixedSizeGrid, GridChildComponentProps } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';
import { Box, Typography, Breadcrumbs, Select, MenuItem, ListItemText, SelectChangeEvent } from '@mui/material';
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
import LauncherModal from './LauncherModal';

const logError = debug('antares:studieslist:error');

const CARD_WIDTH = 380;
const CARD_HEIGHT = 250;
const SPACE = 20;
const TOTAL_CARD_WIDTH = CARD_WIDTH + SPACE;
const TOTAL_CARD_HEIGHT = CARD_HEIGHT + SPACE;

const Cell = React.memo((props: GridChildComponentProps) => {
  const { data, style, columnIndex, rowIndex, isScrolling } = props;
  const { studies, favorite, nbColumns, onFavoriteClick, onLaunchClick, importStudy, deleteStudy, archiveStudy, unarchiveStudy } = data;

  if (studies === undefined || studies.length === 0) return null;

  const study = studies[rowIndex * nbColumns + columnIndex];
  return (
    <Box width={CARD_WIDTH} height={CARD_HEIGHT} display="flex" flexDirection="column" justifyContent="center" alignItems="center" boxSizing="border-box">
      <StudyCard
        key={study.id}
        study={study}
        favorite={favorite.includes(study.id)}
        onFavoriteClick={onFavoriteClick}
        onLaunchClick={() => onLaunchClick(study)}
        onImportStudy={importStudy}
        onArchiveClick={archiveStudy}
        onUnarchiveClick={unarchiveStudy}
        onDeleteClick={deleteStudy}
      />
    </Box>

  );
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
  const [openLaunncherModal, setOpenLauncherModal] = useState<boolean>(false);
  const [currentLaunchStudy, setCurrentLaunchStudy] = useState<StudyMetadata>();
  const [folderList, setFolderList] = useState<Array<string>>([]);
  const [anchorCardMenuEl, setCardMenuAnchorEl] = useState<HTMLButtonElement | null>(null);

  const open = Boolean(anchorCardMenuEl);
  const id = open ? 'simple-popover' : undefined;
  const filterList : Array<GenericInfo> = [
    { id: SortElement.NAME, name: t('studymanager:sortByName') },
    { id: SortElement.DATE, name: t('studymanager:sortByDate') },
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
        <AutoSizer>
          { ({ height, width }) => {
            const COLUMNS = Math.floor(width / TOTAL_CARD_WIDTH);
            const rowRest = studies.length % COLUMNS;
            const ROWS = Math.floor(studies.length / COLUMNS) + (rowRest > 0 ? 1 : 0);
            return (
              <FixedSizeGrid
                height={height}
                width={width}
                columnCount={COLUMNS}
                columnWidth={TOTAL_CARD_WIDTH}
                rowCount={ROWS}
                rowHeight={TOTAL_CARD_HEIGHT}
                style={{ backgroundColor: 'green' }}
                itemData={{ studies, onLaunchClick, nbColumns: COLUMNS, favorite, onFavoriteClick, importStudy, deleteStudy, archiveStudy, unarchiveStudy }}
              >
                {Cell}
              </FixedSizeGrid>
            );
          }
      }
        </AutoSizer>
        {openLaunncherModal && <LauncherModal open={openLaunncherModal} study={currentLaunchStudy} onClose={() => setOpenLauncherModal(false)} />}
      </Box>
    </Box>
  );
}

export default connector(StudiesList);

/* import React, { forwardRef, useEffect, useState } from 'react';
import { AxiosError } from 'axios';
import debug from 'debug';
import { connect, ConnectedProps } from 'react-redux';
import { createStyles, makeStyles, Theme } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { areEqual, FixedSizeList, ListChildComponentProps } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';
import { StudyMetadata } from '../../common/types';
import { removeStudies, updateScrollPosition } from '../../ducks/study';
import { deleteStudy as callDeleteStudy, copyStudy as callCopyStudy, archiveStudy as callArchiveStudy, unarchiveStudy as callUnarchiveStudy } from '../../services/api/study';
import StudyListElementView from './StudyListingItemView';
import StudyDirView from './StudyDirView';
import enqueueErrorSnackbar from '../ui/ErrorSnackBar';
import { AppState } from '../../App/reducers';
import { buildStudyTree } from './utils';
import LauncherModal from '../ui/LauncherModal';

const logError = debug('antares:studyblockview:error');

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flexGrow: 1,
    overflow: 'auto',
  },
  containerGrid: {
    display: 'flex',
    width: '100%',
    flexWrap: 'wrap',
    paddingTop: theme.spacing(2),
    justifyContent: 'space-around',
  },
  containerList: {
    display: 'flex',
    width: '100%',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    paddingTop: theme.spacing(2),
  },
}));

let scrollState = 0;

const LIST_ITEM_HEIGHT = 66.5;

const Row = React.memo((props: ListChildComponentProps) => {
  const { data, index, style } = props;
  const { studies, importStudy, launchStudy, deleteStudy, archiveStudy, unarchiveStudy } = data;
  const study = studies[index];
  return (
    <div style={{ display: 'flex', justifyContent: 'center', ...style, top: `${parseFloat((style || {}).top as string) + 16}px` }}>
      <StudyListElementView
        key={study.id}
        study={study}
        importStudy={importStudy}
        launchStudy={launchStudy}
        deleteStudy={deleteStudy}
        archiveStudy={archiveStudy}
        unarchiveStudy={unarchiveStudy}
      />
    </div>
  );
}, areEqual);

const mapState = (state: AppState) => ({
  scrollPosition: state.study.scrollPosition,
});

const mapDispatch = ({
  removeStudy: (sid: string) => removeStudies([sid]),
  updateScroll: updateScrollPosition,
});

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
interface OwnProps {
  studies: StudyMetadata[];
  setCurrentStudiesLength: (length: number) => void;
  isList: boolean;
}
type PropTypes = PropsFromRedux & OwnProps;

const StudyListing = (props: PropTypes) => {
  const classes = useStyles();
  const { studies, setCurrentStudiesLength, removeStudy, isList, scrollPosition, updateScroll } = props;
  const { enqueueSnackbar } = useSnackbar();
  const [studyToLaunch, setStudyToLaunch] = useState<StudyMetadata|undefined>();
  const [t] = useTranslation();

  const openStudyLauncher = (study: StudyMetadata): void => {
    setStudyToLaunch(study);
  };

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

  const innerElementType = forwardRef<HTMLDivElement, React.DetailedHTMLProps<React.HTMLAttributes<HTMLDivElement>, HTMLDivElement>>((innerProps, ref) => {
    const { style } = innerProps;
    return (
      <div
        ref={ref}
        style={{
          ...style,
          height: `${parseFloat((style || {}).height as string) + 8 * 2}px`,
        }}
      // eslint-disable-next-line react/jsx-props-no-spreading
        {...innerProps}
      />
    );
  });

  useEffect(() =>
    () => {
      updateScroll(scrollState);
    }, [updateScroll]);

  return (
    <div className={classes.root}>
      {
        isList ? (
          <AutoSizer>
            { ({ height, width }) => (
              <FixedSizeList
                initialScrollOffset={scrollPosition * LIST_ITEM_HEIGHT}
                onItemsRendered={({
                  visibleStartIndex,
                }) => { scrollState = visibleStartIndex; }}
                height={height}
                width={width}
                innerElementType={innerElementType}
                itemCount={studies.length}
                itemSize={66}
                itemData={{ studies, importStudy, launchStudy: openStudyLauncher, deleteStudy, archiveStudy, unarchiveStudy }}
              >
                {Row}
              </FixedSizeList>
            )
        }
          </AutoSizer>
        ) : <StudyDirView tree={buildStudyTree(studies)} setCurrentStudiesLength={setCurrentStudiesLength} importStudy={importStudy} launchStudy={openStudyLauncher} deleteStudy={deleteStudy} archiveStudy={archiveStudy} unarchiveStudy={unarchiveStudy} />
      }
      <LauncherModal open={!!studyToLaunch} study={studyToLaunch} close={() => { setStudyToLaunch(undefined); }} />
    </div>
  );
};

export default connector(StudyListing); */
