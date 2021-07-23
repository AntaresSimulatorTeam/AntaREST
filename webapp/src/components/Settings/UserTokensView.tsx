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
import VisibilityIcon from '@material-ui/icons/Visibility';
import DeleteIcon from '@material-ui/icons/HighlightOff';
import ExpandLess from '@material-ui/icons/ExpandLess';
import ExpandMore from '@material-ui/icons/ExpandMore';
import { UserToken } from '../../common/types';

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
    botList: {
      display: 'flex',
      paddingLeft: theme.spacing(4),
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
    },
    userItem: {
      display: 'flex',
      padding: theme.spacing(1),
      paddingLeft: theme.spacing(2),
      flexFlow: 'row nowrap',
      justifyContent: 'space-between',
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
    botItem: {
      display: 'flex',
      padding: theme.spacing(1),
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      color: theme.palette.primary.main,
      backgroundColor: 'white',
      margin: theme.spacing(0.2),
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
    iconsContainer: {
      flex: '1',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-end',
      alignItems: 'center',
    },
    deleteIcon: {
      color: theme.palette.error.light,
      marginLeft: theme.spacing(2),
      marginRight: theme.spacing(2),
      '&:hover': {
        color: theme.palette.error.main,
      },
    },
    seeIcon: {
      color: theme.palette.primary.main,
      '&:hover': {
        color: theme.palette.primary.light,
      },
    },
  }));

interface PropTypes {
  data: Array<UserToken>;
  filter: string;
  onDeleteClick: (userId: number, botId: number) => void;
  onWatchClick: (userId: number, botId: number) => void;
}

const UserTokensView = (props: PropTypes) => {
  const classes = useStyles();
  const { data, filter, onDeleteClick, onWatchClick } = props;
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
    for (let i = 0; i < data.length; i += 1) initToogleList.push(true);
    setToogleList(initToogleList);
  }, [data]);

  return (
    <List component="nav" aria-labelledby="nested-list-subheader" className={classes.root}>
      {data.map(
        (userItem, index) =>
          userItem.bots.length > 0 && (
            <Fragment key={userItem.user.id}>
              <ListItem className={classes.userItem} onClick={() => onButtonChange(index)}>
                <Typography className={clsx(classes.text, classes.title)}>{userItem.user.name}</Typography>
                {toogleList[index] ? <ExpandLess /> : <ExpandMore />}
              </ListItem>
              <Collapse in={toogleList[index]} timeout="auto" unmountOnExit>
                <List component="div" disablePadding className={classes.botList}>
                  {userItem.bots.map(
                    (botItem) =>
                      matchFilter(botItem.name) && (
                        <ListItem key={botItem.id} className={classes.botItem}>
                          <Typography className={classes.text}>{botItem.name}</Typography>
                          <div className={classes.iconsContainer}>
                            <VisibilityIcon className={classes.seeIcon} onClick={() => onWatchClick(userItem.user.id, botItem.id)} />
                            <DeleteIcon className={classes.deleteIcon} onClick={() => onDeleteClick(userItem.user.id, botItem.id)} />
                          </div>
                        </ListItem>
                      ),
                  )}
                </List>
              </Collapse>
            </Fragment>
          ),
      )}
    </List>
  );
};

export default UserTokensView;
