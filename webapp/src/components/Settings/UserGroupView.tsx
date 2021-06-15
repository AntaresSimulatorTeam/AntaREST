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
import { useTranslation } from 'react-i18next';
import { UserGroup } from '../../common/types';
import { roleToString } from '../../services/utils';

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
    userList: {
      display: 'flex',
      paddingLeft: theme.spacing(4),
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
    },
    userItem: {
      backgroundColor: 'white',
      margin: theme.spacing(0.2),
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'space-evenly',
      alignItems: 'center',
    },
    groupItem: {
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
  data: Array<UserGroup>;
  filter: string;
  onDeleteClick: (groupId: string) => void;
  onUpdateClick: (groupId: string) => void;
  onItemClick: (groupId: string) => void;
}

const UserGroupView = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { data, filter, onDeleteClick, onUpdateClick, onItemClick } = props;
  const [toogleList, setToogleList] = useState<Array<boolean>>([]);

  const onButtonChange = (index: number, id: string) => {
    if (index >= 0 && index < toogleList.length) {
      if (!toogleList[index]) onItemClick(id);

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
        (groupItem, index) =>
          matchFilter(groupItem.group.name) && (
            <Fragment key={groupItem.group.id}>
              <ListItem
                className={classes.groupItem}
                button
                onClick={() => onButtonChange(index, groupItem.group.id)}
              >
                <Typography>{groupItem.group.name}</Typography>
                <div className={classes.iconsContainer}>
                  <Button onClick={() => onUpdateClick(groupItem.group.id)}>
                    <CreateIcon className={classes.createIcon} />
                  </Button>
                  <Button onClick={() => onDeleteClick(groupItem.group.id)}>
                    <DeleteIcon className={classes.deleteIcon} />
                  </Button>
                </div>
                {toogleList[index] ? <ExpandLess /> : <ExpandMore />}
              </ListItem>
              <Collapse in={toogleList[index]} timeout="auto" unmountOnExit>
                <List component="div" disablePadding className={classes.userList}>
                  {groupItem.users.map((userItem) => (
                    <ListItem key={userItem.id} className={classes.userItem}>
                      <ListItemText primary={userItem.name} />
                      <Typography>{t(roleToString(userItem.role))}</Typography>
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

export default UserGroupView;
