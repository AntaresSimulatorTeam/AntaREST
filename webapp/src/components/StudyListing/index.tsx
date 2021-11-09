import React, { forwardRef, useEffect } from 'react';
import { AxiosError } from 'axios';
import debug from 'debug';
import { connect, ConnectedProps } from 'react-redux';
import { createStyles, makeStyles, Theme } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { areEqual, FixedSizeGrid, FixedSizeList, GridChildComponentProps, ListChildComponentProps } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';
import { StudyMetadata } from '../../common/types';
import { removeStudies, updateScrollPosition } from '../../ducks/study';
import { deleteStudy as callDeleteStudy, launchStudy as callLaunchStudy, copyStudy as callCopyStudy, archiveStudy as callArchiveStudy, unarchiveStudy as callUnarchiveStudy } from '../../services/api/study';
import StudyListElementView from './StudyListingItemView';
import enqueueErrorSnackbar from '../ui/ErrorSnackBar';
import { AppState } from '../../App/reducers';
import { buildStudyTree } from './utils';

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
const GRID_ITEM_HEIGHT = 206.5;

const Row = React.memo((props: ListChildComponentProps) => {
  const { data, index, style } = props;
  const { studies, isList, importStudy, launchStudy, deleteStudy, archiveStudy, unarchiveStudy } = data;
  const study = studies[index];
  return (
    <div style={{ display: 'flex', justifyContent: 'center', ...style, top: `${parseFloat((style || {}).top as string) + 16}px` }}>
      <StudyListElementView
        key={study.id}
        study={study}
        listMode={isList}
        importStudy={importStudy}
        launchStudy={launchStudy}
        deleteStudy={deleteStudy}
        archiveStudy={archiveStudy}
        unarchiveStudy={unarchiveStudy}
      />
    </div>
  );
}, areEqual);

const Block = (props: GridChildComponentProps) => {
  const { data, rowIndex, columnIndex, style } = props;
  const { studies, isList, importStudy, columnCount, launchStudy, deleteStudy, archiveStudy, unarchiveStudy } = data;
  const study = studies[rowIndex * columnCount + columnIndex];
  if (study) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', ...style, top: `${parseFloat((style || {}).top as string) + 16}px` }}>
        <StudyListElementView
          key={study.id}
          study={study}
          listMode={isList}
          importStudy={importStudy}
          launchStudy={launchStudy}
          deleteStudy={deleteStudy}
          archiveStudy={archiveStudy}
          unarchiveStudy={unarchiveStudy}
        />
      </div>
    );
  }
  return <div />;
};

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
  isList: boolean;
}
type PropTypes = PropsFromRedux & OwnProps;

const StudyListing = (props: PropTypes) => {
  const classes = useStyles();
  const { studies, removeStudy, isList, scrollPosition, updateScroll } = props;
  const { enqueueSnackbar } = useSnackbar();
  const [t] = useTranslation();
  const launchStudy = async (study: StudyMetadata) => {
    try {
      await callLaunchStudy(study.id);
      enqueueSnackbar(t('studymanager:studylaunched', { studyname: study.name }), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('studymanager:failtorunstudy'), { variant: 'error' });
      logError('Failed to launch study', study, e);
    }
  };

  const importStudy = async (study: StudyMetadata, withOutputs = false) => {
    try {
      await callCopyStudy(study.id, `${study.name} (${t('main:copy')})`, withOutputs);
      enqueueSnackbar(t('studymanager:studycopiedsuccess', { studyname: study.name }), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtocopystudy'), e as AxiosError);
      logError('Failed to copy/import study', study, e);
    }
  };

  const archiveStudy = async (study: StudyMetadata) => {
    try {
      await callArchiveStudy(study.id);
      enqueueSnackbar(t('studymanager:archivesuccess', { studyname: study.name }), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:archivefailure', { studyname: study.name }), e as AxiosError);
    }
  };

  const unarchiveStudy = async (study: StudyMetadata) => {
    try {
      await callUnarchiveStudy(study.id);
      enqueueSnackbar(t('studymanager:unarchivesuccess', { studyname: study.name }), { variant: 'success' });
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

  const GridSizer = (gridSizerProps: {width: number; height: number}) => {
    const { width, height } = gridSizerProps;
    const columnCount = Math.floor(width / 428);
    return (
      <FixedSizeGrid
        // eslint-disable-next-line react/prop-types
        initialScrollTop={scrollPosition * GRID_ITEM_HEIGHT}
        onItemsRendered={({
          visibleRowStartIndex,
        }) => { scrollState = visibleRowStartIndex; }}
        height={height}
        width={width}
        innerElementType={innerElementType}
        rowCount={Math.ceil(studies.length / columnCount)}
        columnCount={columnCount}
        rowHeight={206}
        columnWidth={428}
        itemData={{ studies, columnCount, isList, importStudy, launchStudy, deleteStudy, archiveStudy, unarchiveStudy }}
      >
        {Block}
      </FixedSizeGrid>
    );
  };

  useEffect(() =>
    () => {
      updateScroll(scrollState);
    }, [updateScroll]);

  useEffect(() => {
    buildStudyTree(studies);
  }, [studies]);

  return (
    <div className={classes.root}>
      <AutoSizer>
        {
            ({ height, width }) => (isList ? (
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
                itemData={{ studies, isList, importStudy, launchStudy, deleteStudy, archiveStudy, unarchiveStudy }}
              >
                {Row}
              </FixedSizeList>
            ) : (
              <GridSizer width={width} height={height} />
            ))
          }
      </AutoSizer>
    </div>
  );
};

export default connector(StudyListing);
