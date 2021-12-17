import React, { useState, useEffect, Fragment } from 'react';
import { AxiosError } from 'axios';
import {
  makeStyles,
  createStyles,
  Theme,
  Typography,
  List,
  ListItem,
  Collapse,
  Tooltip,
} from '@material-ui/core';
import clsx from 'clsx';
import CreateIcon from '@material-ui/icons/Create';
import DeleteIcon from '@material-ui/icons/HighlightOff';
import ExpandLess from '@material-ui/icons/ExpandLess';
import ExpandMore from '@material-ui/icons/ExpandMore';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import GetAppIcon from '@material-ui/icons/GetApp';
import { MatrixDataSetDTO, MatrixInfoDTO, UserInfo } from '../../common/types';
import { CopyIcon } from './utils';
import enqueueErrorSnackbar from '../ui/ErrorSnackBar';
import DownloadLink from '../ui/DownloadLink';
import { getExportMatrixUrl } from '../../services/api/matrix';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      flex: 'none',
      width: '80%',
      display: 'flex',
      padding: theme.spacing(0),
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      color: theme.palette.primary.main,
      margin: theme.spacing(3),
    },
    matrixList: {
      display: 'flex',
      paddingLeft: theme.spacing(4),
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
    },
    matrixItem: {
      backgroundColor: 'white',
      margin: theme.spacing(0.2),
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      '&:hover': {
        backgroundColor: theme.palette.action.hover,
      },
    },
    datasetItem: {
      display: 'flex',
      padding: theme.spacing(1),
      paddingLeft: theme.spacing(2),
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      color: theme.palette.primary.main,
      backgroundColor: 'white',
      borderRadius: theme.shape.borderRadius,
      borderLeft: `7px solid ${theme.palette.primary.main}`,
      margin: theme.spacing(0.2),
      height: '50px',
      '&:hover': {
        backgroundColor: theme.palette.action.hover,
      },
    },
    iconsContainer: {
      flex: '1',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-end',
      alignItems: 'center',
    },
    title: {
      fontWeight: 'bold',
    },
    text: {
      backgroundColor: theme.palette.action.selected,
      paddingLeft: theme.spacing(1),
      paddingRight: theme.spacing(1),
      borderRadius: theme.shape.borderRadius,
      cursor: 'pointer',
    },
    matrixid: {
      fontFamily: 'monospace',
      color: 'grey',
    },
    deleteIcon: {
      color: theme.palette.error.light,
      marginRight: theme.spacing(2),
      '&:hover': {
        color: theme.palette.error.main,
      },
    },
    createIcon: {
      color: theme.palette.primary.main,
      '&:hover': {
        color: theme.palette.primary.light,
      },
    },
    downloadIcon: {
      color: theme.palette.primary.main,
      marginLeft: theme.spacing(2),
      marginRight: theme.spacing(2),
      '&:hover': {
        color: theme.palette.primary.light,
      },
    },
  }));

interface PropTypes {
  data: Array<MatrixDataSetDTO>;
  filter: string;
  user: UserInfo | undefined;
  onDeleteClick: (datasetId: string) => void;
  onUpdateClick: (datasetId: string) => void;
  onMatrixClick: (matrixInfo: MatrixInfoDTO) => void;
  onDownloadDataset: (datasetId: string) => void;
}

const DataView = (props: PropTypes) => {
  const classes = useStyles();
  const { data, user, filter, onDeleteClick, onUpdateClick, onMatrixClick, onDownloadDataset } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [toogleList, setToogleList] = useState<Array<boolean>>([]);

  const onButtonChange = (index: number) => {
    if (index >= 0 && index < toogleList.length) {
      const tmpList = ([] as Array<boolean>).concat(toogleList);
      tmpList[index] = !tmpList[index];
      setToogleList(tmpList);
    }
  };

  const copyId = (matrixId: string): void => {
    try {
      navigator.clipboard.writeText(matrixId);
      enqueueSnackbar(t('data:onMatrixIdCopySuccess'), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('data:onMatrixIdCopyError'), e as AxiosError);
    }
  };

  const matchFilter = (input: MatrixDataSetDTO): boolean => input.name.search(filter) >= 0 || !!input.matrices.find((matrix: MatrixInfoDTO) => matrix.id.search(filter) >= 0);

  useEffect(() => {
    const initToogleList: Array<boolean> = [];
    for (let i = 0; i < data.length; i += 1) {
      initToogleList.push(false);
    }
    setToogleList(initToogleList);
  }, [data.length]);

  return (
    <List component="nav" aria-labelledby="nested-list-subheader" className={classes.root}>
      {data.map(
        (dataset, index) =>
          matchFilter(dataset) && (
            <Fragment key={dataset.id}>
              <ListItem
                className={classes.datasetItem}
                button
                onClick={() => onButtonChange(index)}
              >
                <Typography className={clsx(classes.text, classes.title)}>{dataset.name}</Typography>
                <div className={classes.iconsContainer}>
                  {
                        user && user.id === dataset.owner.id && (
                        <>
                          <CreateIcon className={classes.createIcon} onClick={(e) => { e.stopPropagation(); onUpdateClick(dataset.id); }} />
                          <GetAppIcon className={classes.downloadIcon} onClick={(e) => { e.stopPropagation(); onDownloadDataset(dataset.id); }} />
                          <DeleteIcon className={classes.deleteIcon} onClick={(e) => { e.stopPropagation(); onDeleteClick(dataset.id); }} />
                        </>
                        )}
                </div>
                {toogleList[index] ? <ExpandLess /> : <ExpandMore />}
              </ListItem>
              <Collapse in={toogleList[index]} timeout="auto" unmountOnExit>
                <List component="div" disablePadding className={classes.matrixList}>
                  {dataset.matrices.map((matrixItem) => (
                    <ListItem
                      key={matrixItem.name}
                      className={classes.matrixItem}
                    >
                      <Tooltip title={t('data:copyid') as string} placement="top">
                        <CopyIcon style={{ marginRight: '0.5em', cursor: 'pointer' }} onClick={() => copyId(matrixItem.id)} />
                      </Tooltip>
                      <Tooltip title={matrixItem.id} placement="top">
                        <Typography onClick={() => onMatrixClick(matrixItem)} className={classes.text}>{matrixItem.name}</Typography>
                      </Tooltip>
                      <div style={{ flex: 1, display: 'flex', flexFlow: 'row nowrap', justifyContent: 'flex-end' }}>
                        <DownloadLink url={getExportMatrixUrl(matrixItem.id)}>
                          <GetAppIcon className={classes.downloadIcon} />
                        </DownloadLink>
                      </div>
                    </ListItem>
                  ))}
                </List>
              </Collapse>
            </Fragment>
          ),
      )}
    </List>
  );
};

export default DataView;
