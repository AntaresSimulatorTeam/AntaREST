import React, { Fragment } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  Typography,
  List,
  ListItem,
} from '@material-ui/core';
import CreateIcon from '@material-ui/icons/Create';
import VisibilityIcon from '@material-ui/icons/Visibility';
import DeleteIcon from '@material-ui/icons/HighlightOff';
import { UserDTO, BotDTO, MatrixDataSetDTO, IDType } from '../../common/types';

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
    userItem: {
      display: 'flex',
      padding: theme.spacing(1),
      paddingLeft: theme.spacing(2),
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      color: theme.palette.primary.main,
      backgroundColor: 'white',
      borderRadius: theme.shape.borderRadius,
      border: `1px solid ${theme.palette.action.focus}`,
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
    text: {
      backgroundColor: theme.palette.action.selected,
      fontWeight: 'bold',
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
    actionIcon: {
      color: theme.palette.primary.main,
      '&:hover': {
        color: theme.palette.primary.light,
      },
    },
  }));

interface PropTypes {
  data: Array<UserDTO | BotDTO | MatrixDataSetDTO>;
  filter: string;
  view: boolean;
  excludeName?: Array<string>;
  onDeleteClick: (id: IDType) => void;
  onActionClick: (id: IDType) => void;
}

const GenericListView = (props: PropTypes) => {
  const classes = useStyles();
  const { data, view, excludeName, filter, onDeleteClick, onActionClick } = props;

  const matchFilter = (input: string): boolean =>
    // Very basic search => possibly modify
    input.search(filter) >= 0;

  return (
    <List component="nav" aria-labelledby="nested-list-subheader" className={classes.root}>
      {data.map(
        (item) =>
          item.name &&
          !excludeName?.find((elm) => elm === item.name) &&
          matchFilter(item.name) && (
            <Fragment key={item.id}>
              <ListItem className={classes.userItem}>
                <Typography className={classes.text}>{item.name}</Typography>
                <div className={classes.iconsContainer}>
                  {view ? (
                    <VisibilityIcon className={classes.actionIcon} onClick={() => onActionClick(item.id)} />
                  ) : (
                    <CreateIcon className={classes.actionIcon} onClick={() => onActionClick(item.id)} />
                  )}
                  <DeleteIcon className={classes.deleteIcon} onClick={() => onDeleteClick(item.id)} />
                </div>
              </ListItem>
            </Fragment>
          ),
      )}
    </List>
  );
};

GenericListView.defaultProps = {
  excludeName: [],
};

export default GenericListView;
