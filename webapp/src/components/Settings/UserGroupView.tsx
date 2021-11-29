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
import CloseRoundedIcon from '@material-ui/icons/CloseRounded';
import ExpandLess from '@material-ui/icons/ExpandLess';
import ExpandMore from '@material-ui/icons/ExpandMore';
import { useTranslation } from 'react-i18next';
import { GroupDTO, RoleType, UserGroup, UserRoleDTO } from '../../common/types';
import { roleToString } from '../../services/utils';
import RoleModal from './Groups/RoleModal';

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
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    groupItem: {
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
    role: {
      backgroundColor: theme.palette.primary.main,
      color: 'white',
      marginRight: theme.spacing(2),
      paddingLeft: theme.spacing(1),
      paddingRight: theme.spacing(1),
      borderRadius: theme.shape.borderRadius,
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
      marginRight: theme.spacing(2),
      '&:hover': {
        color: theme.palette.primary.light,
      },
    },
    endItem: {
      display: 'flex',
      padding: theme.spacing(0),
      flexFlow: 'row nowrap',
      justifyContent: 'center',
      alignItems: 'center',
    },
  }));

interface PropTypes {
  data: Array<UserGroup>;
  filter: string;
  onDeleteGroupClick?: (groupId: string) => void;
  onDeleteUserClick: (groupId: string, userId: number) => void;
  onUpdateClick: (groupId: string) => void;
  onItemClick: (groupId: string) => void;
  onUpdateRole: (groupId: string, userId: number, role: RoleType) => void;
}

interface UserSelection {
  group: GroupDTO | undefined;
  user: UserRoleDTO | undefined;
}

const UserGroupView = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { data, filter, onDeleteGroupClick, onDeleteUserClick, onUpdateClick, onItemClick, onUpdateRole } = props;
  const [toogleList, setToogleList] = useState<Array<boolean>>([]);
  const [userRoleModal, setUserRoleModal] = useState<UserSelection>({ group: undefined, user: undefined });

  const onButtonChange = (index: number, id: string) => {
    if (index >= 0 && index < toogleList.length) {
      if (!toogleList[index]) onItemClick(id);

      const tmpList = ([] as Array<boolean>).concat(toogleList);
      tmpList[index] = !tmpList[index];
      setToogleList(tmpList);
    }
  };

  const onUserUpdateRole = (groupId: string, userId: number, role: RoleType): void => {
    onUpdateRole(groupId, userId, role);
    setUserRoleModal({ group: undefined, user: undefined });
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
                <Typography className={clsx(classes.text, classes.title)}>{groupItem.group.name}</Typography>
                <div className={classes.iconsContainer}>
                  <CreateIcon className={classes.createIcon} onClick={() => onUpdateClick(groupItem.group.id)} />
                  {onDeleteGroupClick !== undefined && <DeleteIcon className={classes.deleteIcon} onClick={() => onDeleteGroupClick(groupItem.group.id)} />}
                </div>
                {toogleList[index] ? <ExpandLess /> : <ExpandMore />}
              </ListItem>
              <Collapse in={toogleList[index]} timeout="auto" unmountOnExit>
                <List component="div" disablePadding className={classes.userList}>
                  {groupItem.users.map((userItem) => (
                    <ListItem key={userItem.id} className={classes.userItem}>
                      <Typography className={classes.text}>{userItem.name}</Typography>
                      <div className={classes.endItem}>
                        <Typography className={classes.role}>{t(roleToString(userItem.role))}</Typography>
                        <CreateIcon className={classes.createIcon} style={{ cursor: 'pointer' }} onClick={() => setUserRoleModal({ group: groupItem.group, user: userItem })} />
                        <CloseRoundedIcon className={classes.deleteIcon} style={{ cursor: 'pointer' }} onClick={() => onDeleteUserClick(groupItem.group.id, userItem.id)} />
                      </div>
                    </ListItem>
                  ))}
                </List>
              </Collapse>
              <RoleModal
                open={userRoleModal.user !== undefined}
                onClose={() => setUserRoleModal({ group: undefined, user: undefined })}
                onSave={onUserUpdateRole}
                group={userRoleModal.group}
                user={userRoleModal.user as UserRoleDTO}
              />
            </Fragment>
          ),
      )}
    </List>
  );
};

UserGroupView.defaultProps = {
  onDeleteGroupClick: undefined,
};

export default UserGroupView;
