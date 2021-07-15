import React, { useState, useEffect, Fragment } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  Collapse,
} from '@material-ui/core';
import CreateIcon from '@material-ui/icons/Create';
import DeleteIcon from '@material-ui/icons/Delete';

import ExpandLess from '@material-ui/icons/ExpandLess';
import ExpandMore from '@material-ui/icons/ExpandMore';
import { MatrixDataSetDTO } from '../../common/types';

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
      justifyContent: 'space-evenly',
      alignItems: 'center',
    },
    datasetItem: {
      display: 'flex',
      padding: theme.spacing(1),
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      color: theme.palette.primary.main,
      backgroundColor: 'white',
      border: `1px solid ${theme.palette.primary.main}`,
      margin: theme.spacing(0.2),
    },
    iconsContainer: {
      flex: '1',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-end',
      alignItems: 'center',
    },
    deleteIcon: {
      color: theme.palette.error.main,
    },
    createIcon: {
      color: theme.palette.primary.main,
    },
  }));

interface PropTypes {
  data: Array<MatrixDataSetDTO>;
  filter: string;
  onDeleteClick: (datasetId: string) => void;
  onUpdateClick: (datasetId: string) => void;
  onMatrixClick: (datasetId: string, matrixId: string) => void;
}

const DataView = (props: PropTypes) => {
  const classes = useStyles();
  const { data, filter, onDeleteClick, onUpdateClick, onMatrixClick } = props;
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
                <Typography>{dataset.name}</Typography>
                <div className={classes.iconsContainer}>
                  <Button onClick={() => onUpdateClick(dataset.id)}>
                    <CreateIcon className={classes.createIcon} />
                  </Button>
                  <Button onClick={() => onDeleteClick(dataset.id)}>
                    <DeleteIcon className={classes.deleteIcon} />
                  </Button>
                </div>
                {toogleList[index] ? <ExpandLess /> : <ExpandMore />}
              </ListItem>
              <Collapse in={toogleList[index]} timeout="auto" unmountOnExit>
                <List component="div" disablePadding className={classes.matrixList}>
                  {dataset.matrix.map((matrixItem) => (
                    <ListItem key={matrixItem.id} className={classes.matrixItem}>
                      <ListItemText
                        primary={matrixItem.name}
                        onClick={() => onMatrixClick(dataset.id, matrixItem.id)}
                      />
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
