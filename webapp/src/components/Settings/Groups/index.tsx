/* eslint-disable @typescript-eslint/camelcase */
import React, { useState, useEffect } from 'react';
import { AxiosError } from 'axios';
import { connect, ConnectedProps } from 'react-redux';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { AppState } from '../../../App/reducers';
import GenericListingView from '../../ui/NavComponents/GenericListingView';
import GroupModal from './GroupModal';
import { getGroups, createGroup, updateGroup, deleteGroup, getGroupInfos, deleteUserRole, createRole } from '../../../services/api/user';
import { RoleCreationDTO, RoleType, UserGroup, UserRoleDTO } from '../../../common/types';
import ConfirmationModal from '../../ui/ConfirmationModal';
import UserGroupView from '../UserGroupView';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';
import { isUserAdmin } from '../../../services/utils';

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const connector = connect(mapState);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

interface UserDeletion {
  groupId: string;
  userId: number;
}

interface DeletionInfo {
  type: 'user' | 'group';
  data: string | UserDeletion;
}

const GroupsSettings = (props: PropTypes) => {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();

  // Group modal
  const [openModal, setOpenModal] = useState<boolean>(false);
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);
  const [groupList, setGroupList] = useState<Array<UserGroup>>([]);
  const [selectedGroup, setActiveGroup] = useState<UserGroup>();
  const [deletionInfo, setDeletionInfo] = useState<DeletionInfo>({ type: 'group', data: '' });
  const [isAdmin, setIsAdmin] = useState<boolean>(false);
  const [filter, setFilter] = useState<string>('');
  const { user } = props;

  const createNewGroup = () => {
    setOpenModal(true);
    setActiveGroup(undefined);
  };

  const onDeleteGroupClick = (id: string) => {
    setDeletionInfo({ type: 'group', data: id });
    setOpenConfirmationModal(true);
  };

  const onDeleteUserClick = (groupId: string, userId: number) => {
    setDeletionInfo({ type: 'user', data: { groupId, userId } });
    setOpenConfirmationModal(true);
  };

  const manageUserDeletion = async () => {
    try {
      const data: UserDeletion = deletionInfo.data as UserDeletion;
      await deleteUserRole(data.groupId, data.userId);
      const tmpList = ([] as Array<UserGroup>).concat(groupList);
      const groupIndex = tmpList.findIndex((item) => item.id === data.groupId);
      if (groupIndex >= 0) {
        tmpList[groupIndex].users = tmpList[groupIndex].users.filter((item) => item.id !== data.userId);
        setGroupList(tmpList);
        enqueueSnackbar(t('settings:onUserDeleteSuccess'), { variant: 'success' });
      }
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('settings:onUserDeleteError'), e as AxiosError);
    }
    setDeletionInfo({ type: 'group', data: '' });
    setOpenConfirmationModal(false);
  };

  const manageGroupDeletion = async () => {
    try {
      // 1) Call backend (Delete)
      const deletedGroupId = await deleteGroup(deletionInfo.data as string);
      // 2) Delete group locally from groupList
      setGroupList(groupList.filter((item) => item.id !== deletedGroupId));
      enqueueSnackbar(t('settings:onGroupDeleteSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('settings:onGroupDeleteError'), e as AxiosError);
    }
    setDeletionInfo({ type: 'group', data: '' });
    setOpenConfirmationModal(false);
  };

  const onUpdateRole = async (groupId: string, userId: number, role: RoleType) => {
    try {
      const roleCreation: RoleCreationDTO = {
        group_id: groupId,
        identity_id: userId,
        type: role,
      };
      const tmpList = ([] as Array<UserGroup>).concat(groupList);
      const groupIndex = tmpList.findIndex((item) => item.id === groupId);
      if (groupIndex >= 0) {
        const userIndex = tmpList[groupIndex].users.findIndex((item) => item.id === userId);
        if (userIndex >= 0) {
          await deleteUserRole(groupId, userId);
          await createRole(roleCreation);
          tmpList[groupIndex].users[userIndex].role = role;
          setGroupList(tmpList);
          enqueueSnackbar(t('settings:onUserUpdate'), { variant: 'success' });
        }
      }
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('settings:onUserSaveError'), e as AxiosError);
    }
  };

  const getGroupUsers = async (groupId: string): Promise<UserGroup | undefined> => {
    try {
      const tmpList = ([] as Array<UserGroup>).concat(groupList);
      const groupInfos = await getGroupInfos(groupId);
      const index = tmpList.findIndex((item) => item.id === groupInfos.id);
      if (index >= 0) {
        tmpList[index] = { ...groupInfos, users: groupInfos.users.filter((elm) => elm.id !== user?.id) };
        setGroupList(tmpList);
        return tmpList[index];
      }
      enqueueSnackbar(t('settings:groupInfosError'), { variant: 'error' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('settings:groupInfosError'), e as AxiosError);
    }
    return undefined;
  };

  const onItemClick = async (groupId: string) => {
    await getGroupUsers(groupId);
  };

  const onUpdateClick = async (groupId: string) => {
    const groupFound = await getGroupUsers(groupId);

    if (groupFound) {
      setActiveGroup(groupFound);
      setOpenModal(true);
    }
  };

  const onModalClose = () => {
    setOpenModal(false);
  };

  const onModalSave = async (name: string, userList: Array<UserRoleDTO>) => {
    try {
      if (selectedGroup) {
        if (selectedGroup.name !== name) {
          const updatedGroup = await updateGroup(selectedGroup.id, name);
          const tmpList = ([] as Array<UserGroup>).concat(groupList);
          const index = tmpList.findIndex((item) => item.id === selectedGroup.id);
          if (index < 0) return;
          tmpList[index].name = updatedGroup.name;
          setGroupList(tmpList);
        }

        Promise.all(
          userList.map(async (item) => {
            const role: RoleCreationDTO = {
              group_id: selectedGroup.id,
              identity_id: item.id,
              type: item.role,
            };
            await createRole(role);
          }),
        );
        enqueueSnackbar(t('settings:onGroupUpdate'), { variant: 'success' });
      } else {
        const newGroup = await createGroup(name);
        const newGroupItem: UserGroup = {
          ...newGroup,
          users: [],
        };
        setGroupList(groupList.concat(newGroupItem));
        setActiveGroup(newGroupItem);
        Promise.all(
          userList.map(async (item) => {
            const role: RoleCreationDTO = {
              group_id: newGroup.id,
              identity_id: item.id,
              type: item.role,
            };
            await createRole(role);
          }),
        );
        enqueueSnackbar(t('settings:onGroupCreation'), { variant: 'success' });
      }
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('settings:onGroupSaveError'), e as AxiosError);
    }
    onModalClose();
  };

  useEffect(() => {
    let tmpIsAdmin = false;
    if (user !== undefined) tmpIsAdmin = isUserAdmin(user);
    const init = async () => {
      if (user !== undefined) {
        let groups: Array<UserGroup> = [];
        if (tmpIsAdmin) {
          try {
            const res = await getGroups();
            groups = res
              .filter((item) => item.id !== 'admin')
              .map((group) => ({ ...group, users: [] }));
          } catch (e) {
            enqueueErrorSnackbar(enqueueSnackbar, t('settings:groupsError'), e as AxiosError);
          }
        } else {
          groups = user.groups
            .filter((item) => item.role === RoleType.ADMIN)
            .map((group) => ({ id: group.id, name: group.name, users: [] }));
        }
        setGroupList(groups);
      }
    };
    init();
    setIsAdmin(tmpIsAdmin);
  }, [user, t, enqueueSnackbar]);

  return (
    <GenericListingView
      searchFilter={(input: string) => setFilter(input)}
      placeholder={t('settings:groupsSearchbarPlaceholder')}
      buttonValue={t('settings:createGroup')}
      onButtonClick={isAdmin ? createNewGroup : undefined}
    >
      <UserGroupView
        data={groupList}
        filter={filter}
        onDeleteGroupClick={isAdmin ? onDeleteGroupClick : undefined}
        onDeleteUserClick={onDeleteUserClick}
        onUpdateClick={onUpdateClick}
        onItemClick={onItemClick}
        onUpdateRole={onUpdateRole}
      />
      {openModal && (
        <GroupModal
          open={openModal}
          isAdmin={isAdmin}
          onClose={onModalClose}
          onSave={onModalSave}
          group={selectedGroup}
          userId={user?.id}
        />
      )}
      {openConfirmationModal && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={deletionInfo.type === 'group' ? t('settings:deleteGroupConfirmation') : t('settings:removeUserFromGroup')}
          handleYes={deletionInfo.type === 'group' ? manageGroupDeletion : manageUserDeletion}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
    </GenericListingView>
  );
};

export default connector(GroupsSettings);
