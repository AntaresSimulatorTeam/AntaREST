import React, { useState, useEffect } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { AppState } from '../../../reducers';
import GenericSettingView from '../../../../components/Settings/GenericSettingView';
import GroupModal from './GroupModal';
import { getGroups, createGroup, updateGroup, deleteGroup, getGroupInfos } from '../../../../services/api/user';
import { GroupDTO, UserGroup } from '../../../../common/types';
import ConfirmationModal from '../../../../components/ui/ConfirmationModal';
import UserGroupView from '../../../../components/Settings/UserGroupView';

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const connector = connect(mapState);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const GroupsSettings = (props: PropTypes) => {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();

  // Group modal
  const [openModal, setOpenModal] = useState<boolean>(false);
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);
  const [groupList, setGroupList] = useState<Array<UserGroup>>([]);
  const [selectedGroup, setActiveGroup] = useState<GroupDTO>();
  const [idForDeletion, setIdForDeletion] = useState<string>('');
  const [filter, setFilter] = useState<string>('');
  const { user } = props;

  const createNewGroup = () => {
    setOpenModal(true);
    setActiveGroup(undefined);
  };

  const onUpdateClick = (groupId: string) => {
    const groupFound = groupList.find((item) => item.group.id === groupId);

    if (groupFound) {
      setActiveGroup(groupFound.group);
      setOpenModal(true);
    }
  };

  const onDeleteClick = (id: string) => {
    setIdForDeletion(id);
    setOpenConfirmationModal(true);
  };

  const manageGroupDeletion = async () => {
    try {
      // 1) Call backend (Delete)
      const deletedGroupId = await deleteGroup(idForDeletion as string);
      // 2) Delete group locally from groupList
      setGroupList(groupList.filter((item) => item.group.id !== deletedGroupId));
      enqueueSnackbar(t('settings:onGroupDeleteSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('settings:onGroupDeleteError'), { variant: 'error' });
    }
    setIdForDeletion('');
    setOpenConfirmationModal(false);
  };

  const onItemClick = async (groupId: string) => {
    const tmpList = ([] as Array<UserGroup>).concat(groupList);
    const groupInfos = await getGroupInfos(groupId);
    const index = tmpList.findIndex((item) => item.group.id === groupInfos.group.id);
    if (index >= 0) {
      tmpList[index] = groupInfos;
      setGroupList(tmpList);
    } else {
      // SNACKBAR
    }
  };

  const onModalClose = () => {
    setOpenModal(false);
  };

  const onModalSave = async (name: string) => {
    try {
      if (selectedGroup) {
        if (selectedGroup.name === name) return;

        const updatedGroup = await updateGroup(selectedGroup.id, name);
        const tmpList = ([] as Array<UserGroup>).concat(groupList);
        const index = tmpList.findIndex((item) => item.group.id === selectedGroup.id);
        if (index >= 0) {
          tmpList[index].group.name = updatedGroup.name;
          setGroupList(tmpList);
          enqueueSnackbar(t('settings:onGroupUpdate'), { variant: 'success' });
        }
      } else {
        const newGroup = await createGroup(name);
        const newGroupItem: UserGroup = {
          group: newGroup,
          users: [],
        };
        setGroupList(groupList.concat(newGroupItem));
        setActiveGroup(newGroup);
        enqueueSnackbar(t('settings:onGroupCreation'), { variant: 'success' });
      }
    } catch (e) {
      enqueueSnackbar(t('settings:onGroupSaveError'), { variant: 'error' });
    }
    onModalClose();
  };

  useEffect(() => {
    const init = async () => {
      try {
        const res = await getGroups();
        const groups = res
          .filter((item) => item.id !== 'admin')
          .map((group) => ({ group, users: [] }));
        setGroupList(groups);
      } catch (e) {
        enqueueSnackbar(t('settings:groupsError'), { variant: 'error' });
      }
    };
    init();
  }, [user, t, enqueueSnackbar]);

  return (
    <GenericSettingView
      searchFilter={(input: string) => setFilter(input)}
      placeholder={t('settings:groupsSearchbarPlaceholder')}
      buttonValue={t('settings:createGroup')}
      onButtonClick={createNewGroup}
    >
      <UserGroupView
        data={groupList}
        filter={filter}
        onDeleteClick={onDeleteClick}
        onUpdateClick={onUpdateClick}
        onItemClick={onItemClick}
      />
      {openModal && (
        <GroupModal
          open={openModal}
          onClose={onModalClose}
          onSave={onModalSave}
          group={selectedGroup}
        />
      )}
      {openConfirmationModal && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={t('settings:deleteGroupConfirmation')}
          handleYes={manageGroupDeletion}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
    </GenericSettingView>
  );
};

export default connector(GroupsSettings);
