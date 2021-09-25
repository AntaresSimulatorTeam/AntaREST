/* eslint-disable @typescript-eslint/camelcase */
import React, { useState, useEffect } from 'react';
import { createStyles, makeStyles, Theme, TextField } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import GenericModal from '../../ui/GenericModal';
import GroupsAssignmentView from '../GroupsAssignmentView';
import { getGroups, getUserInfos } from '../../../services/api/user';
import { GroupDTO, RoleType, RoleDTO, UserDTO } from '../../../common/types';
import { saveUser } from './utils';

const useStyles = makeStyles((theme: Theme) => createStyles({
  infos: {
    flex: '1',
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    padding: theme.spacing(2),
  },
  idFields: {
    width: '70%',
    height: '30px',
    boxSizing: 'border-box',
    margin: theme.spacing(2),
  },
}));

interface PropTypes {
    open: boolean;
    userInfos: UserDTO | undefined;
    onNewUserCreaion: (newUser: UserDTO) => void;
    onClose: () => void;
}

const UserModal = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { open, userInfos, onNewUserCreaion, onClose } = props;
  const [groupList, setGroupList] = useState<Array<GroupDTO>>([]);
  const [roleList, setRoleList] = useState<Array<RoleDTO>>([]);
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [selectedGroup, setActiveGroup] = useState<GroupDTO>();

  const onChange = (group: GroupDTO) => {
    setActiveGroup(group);
  };

  const addRoleToList = () => {
    // 1) Look if role is already added to list
    if (selectedGroup && !roleList.find((item) => item.group_id === selectedGroup.id)) {
      // 2) Create a new role with type == READER
      const newRole: RoleDTO = {
        group_id: selectedGroup.id,
        group_name: selectedGroup.name,
        identity_id: userInfos ? userInfos.id : -1,
        type: RoleType.READER, // READER by default
      };
      // 3) Add the role in roleList
      setRoleList(roleList.concat([newRole]));
    }
  };

  const deleteRoleFromList = (groupId: string) => {
    // Delete role from roleList
    const tmpList = roleList.filter((item) => item.group_id !== groupId);
    setRoleList(tmpList);
  };

  // Update Role in roleList
  const updateRoleFromList = (groupId: string, type: RoleType) => {
    // 1) Find the role
    const tmpList: Array<RoleDTO> = ([] as Array<RoleDTO>).concat(roleList);
    const index = roleList.findIndex((item) => item.group_id === groupId);
    if (index >= 0) {
      // 2) Update role in roleList
      tmpList[index].type = type;
      setRoleList(tmpList);
    }
  };

  const onSave = async () => {
    try {
      await saveUser(username, password, roleList, onNewUserCreaion, userInfos);
      if (userInfos) enqueueSnackbar(t('settings:onUserUpdate'), { variant: 'success' });
      else enqueueSnackbar(t('settings:onUserCreation'), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('settings:onUserSaveError'), { variant: 'error' });
    }
    onClose();
  };

  useEffect(() => {
    const init = async () => {
      try {
        // 1) Get list of all groups and add it to groupList or locally from access_token
        const groups = await getGroups();
        const filteredGroup = groups.filter((item) => item.id !== 'admin');
        setGroupList(filteredGroup);

        if (filteredGroup.length > 0) setActiveGroup(filteredGroup[0]);

        // 2) If userInfos exist => get list of user roles and update roleList
        if (userInfos) {
          const users = await getUserInfos(userInfos.id);
          const filteredRoles = users.roles.filter((item) => item.group_id !== 'admin');
          setRoleList(filteredRoles);
        }
      } catch (e) {
        enqueueSnackbar(t('settings:groupsError'), { variant: 'error' });
      }
    };
    init();
    return () => {
      setGroupList([]);
      setRoleList([]);
      setActiveGroup(undefined);
    };
  }, [userInfos, t, enqueueSnackbar]);

  return (
    <GenericModal
      open={open}
      handleClose={onClose}
      handleSave={onSave}
      title={userInfos ? userInfos.name : t('settings:newUserTitle')}
    >
      {
                !userInfos &&
                (
                <div className={classes.infos}>
                  <TextField
                    className={classes.idFields}
                    value={username}
                    onChange={(event) => setUsername(event.target.value as string)}
                    label={t('settings:usernameLabel')}
                    variant="outlined"
                  />
                  <TextField
                    className={classes.idFields}
                    label={t('settings:passwordLabel')}
                    value={password}
                    onChange={(event) => setPassword(event.target.value as string)}
                    type="password"
                    variant="outlined"
                  />
                </div>
                )

            }
      {
                !!selectedGroup && (
                <GroupsAssignmentView
                  groupsList={groupList}
                  roleList={roleList}
                  selectedGroup={selectedGroup}
                  onChange={onChange}
                  addRole={addRoleToList}
                  deleteRole={deleteRoleFromList}
                  updateRole={updateRoleFromList}
                />
                )}
    </GenericModal>
  );
};

export default UserModal;
