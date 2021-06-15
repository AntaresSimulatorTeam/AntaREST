import React from 'react';
import { createStyles, makeStyles, Theme, Button, Paper, Typography } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import MenuItem from '@material-ui/core/MenuItem';
import Select from '@material-ui/core/Select';
import CloseIcon from '@material-ui/icons/Close';
import { GroupDTO, RoleType, RoleDTO, JWTGroup } from '../../common/types';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '300px',
      height: '250px',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      marginTop: theme.spacing(1),
      padding: theme.spacing(1),
      overflow: 'hidden',
    },
    titleBox: {
      width: '100%',
      paddingLeft: theme.spacing(2),
    },
    title: {
      color: theme.palette.primary.main,
    },
    groupsList: {
      width: '100%',
      height: '60px',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      overflow: 'hidden',
      margin: theme.spacing(1),
    },
    select: {
      margin: theme.spacing(2),
    },
    roleList: {
      width: '90%',
      flex: '1',
      overflow: 'auto',
      padding: theme.spacing(1),
      display: 'flex',
      flexFlow: 'column nowrap',
      alignItems: 'center',
    },
    role: {
      flex: 'none',
      height: '40px',
      width: '100%',
      margin: theme.spacing(0.1),
      padding: theme.spacing(1),
      boxSizing: 'border-box',
      display: 'flex',
      flexFlow: 'row nowrap',
      alignItems: 'center',
    },
    close: {
      color: theme.palette.error.main,
      marginLeft: theme.spacing(1),
      marginRight: theme.spacing(1),
    },
  }));

interface PropTypes {
  groupsList: Array<GroupDTO>;
  userGroups?: Array<JWTGroup>;
  selectedGroup?: GroupDTO;
  roleList: Array<RoleDTO>;
  onChange: (group: GroupDTO) => void;
  addRole: () => void;
  deleteRole: (groupId: string) => void;
  updateRole: (groupId: string, type: RoleType) => void;
}

const GroupsAssignmentView = (props: PropTypes) => {
  const {
    groupsList,
    userGroups,
    selectedGroup,
    onChange,
    roleList,
    addRole,
    deleteRole,
    updateRole,
  } = props;
  const classes = useStyles();
  const [t] = useTranslation();

  const getMenuItems = (id: string) => {
    const menuItems = [
      { role: RoleType.READER, tr: 'settings:readerRole' },
      { role: RoleType.WRITER, tr: 'settings:writerRole' },
      { role: RoleType.RUNNER, tr: 'settings:runnerRole' },
      { role: RoleType.ADMIN, tr: 'settings:adminRole' },
    ];
    if (userGroups) {
      const groupFound = userGroups.find((group) => group.id === id);
      if (groupFound) {
        return menuItems.filter((item) => groupFound.role >= item.role);
      }
    }

    return menuItems;
  };

  if (selectedGroup === undefined) {
    return (
      <div className={classes.root}>
        <div className={classes.titleBox}>
          <Typography className={classes.title}>{t('settings:permissionsLabel')}</Typography>
        </div>
      </div>
    );
  }
  return (
    <div className={classes.root}>
      <div className={classes.titleBox}>
        <Typography className={classes.title}>{t('settings:permissionsLabel')}</Typography>
      </div>
      <div className={classes.groupsList}>
        <Select
          value={selectedGroup?.id}
          onChange={(event: React.ChangeEvent<{ value: unknown }>) =>
            onChange(groupsList.find((elm) => event.target.value === elm.id) as GroupDTO)
          }
          label={t('settings:groupNameLabel')}
          className={classes.select}
        >
          {groupsList.map((item) => (
            <MenuItem key={item.id} value={item.id}>
              {item.name}
            </MenuItem>
          ))}
        </Select>
        <Button variant="contained" color="primary" onClick={addRole}>
          {t('settings:addButton')}
        </Button>
      </div>
      <div className={classes.roleList}>
        {roleList.map((item) => (
          <Paper key={item.group_id} className={classes.role}>
            <CloseIcon className={classes.close} onClick={() => deleteRole(item.group_id)} />
            <Typography>{item.group_name}</Typography>
            <Select
              value={item.type}
              onChange={(event: React.ChangeEvent<{ value: unknown }>) =>
                updateRole(item.group_id, event.target.value as RoleType)
              }
              label={t('settings:roleLabel')}
              className={classes.select}
            >
              {getMenuItems(item.group_id).map((menuItem) => (
                <MenuItem key={menuItem.role} value={menuItem.role}>
                  {t(menuItem.tr)}
                </MenuItem>
              ))}
            </Select>
          </Paper>
        ))}
      </div>
    </div>
  );
};

GroupsAssignmentView.defaultProps = {
  userGroups: [],
  selectedGroup: undefined,
};

export default GroupsAssignmentView;
