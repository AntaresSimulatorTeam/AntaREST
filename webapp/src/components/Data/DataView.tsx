import React, { useState, useEffect, Fragment } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  Typography,
  List,
  ListItem,
  Collapse,
} from '@material-ui/core';
import clsx from 'clsx';
import CreateIcon from '@material-ui/icons/Create';
import DeleteIcon from '@material-ui/icons/HighlightOff';
import ExpandLess from '@material-ui/icons/ExpandLess';
import ExpandMore from '@material-ui/icons/ExpandMore';
import { MatrixDataSetDTO, MatrixInfoDTO, UserInfo } from '../../common/types';

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
    },
    deleteIcon: {
      color: theme.palette.error.light,
      marginLeft: theme.spacing(2),
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
  }));

interface PropTypes {
  data: Array<MatrixDataSetDTO>;
  filter: string;
  user: UserInfo | undefined;
  onDeleteClick: (datasetId: string) => void;
  onUpdateClick: (datasetId: string) => void;
  onMatrixClick: (matrixInfo: MatrixInfoDTO) => void;
}

const DataView = (props: PropTypes) => {
  const classes = useStyles();
  const { data, user, filter, onDeleteClick, onUpdateClick, onMatrixClick } = props;
  const [toogleList, setToogleList] = useState<Array<boolean>>([]);

  const onButtonChange = (index: number) => {
    if (index >= 0 && index < toogleList.length) {
      const tmpList = ([] as Array<boolean>).concat(toogleList);
      tmpList[index] = !tmpList[index];
      setToogleList(tmpList);
    }
  };

  const matchFilter = (input: string): boolean =>
    // Very basic search => possibly modify
    input.search(filter) >= 0;

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
          matchFilter(dataset.name) && (
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
                          <CreateIcon className={classes.createIcon} onClick={() => onUpdateClick(dataset.id)} />
                          <DeleteIcon className={classes.deleteIcon} onClick={() => onDeleteClick(dataset.id)} />
                        </>
                        )}
                </div>
                {toogleList[index] ? <ExpandLess /> : <ExpandMore />}
              </ListItem>
              <Collapse in={toogleList[index]} timeout="auto" unmountOnExit>
                <List component="div" disablePadding className={classes.matrixList}>
                  {dataset.matrices.map((matrixItem) => (
                    <ListItem
                      key={matrixItem.id}
                      className={classes.matrixItem}
                      onClick={() => onMatrixClick(matrixItem)}
                    >
                      <Typography className={classes.text}>{matrixItem.name}</Typography>
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
