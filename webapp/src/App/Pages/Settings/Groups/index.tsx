import React, { useState, useEffect } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { AppState } from '../../../reducers';
import GenericSettingView from '../../../../components/Settings/GenericSettingView';
import ItemSettings from '../../../../components/Settings/ItemSettings';
import GroupModal from './GroupModal'
import { getGroups, createGroup, updateGroup, deleteGroup} from '../../../../services/api/user';
import {GroupDTO, IDType } from '../../../../common/types';
import ConfirmationModal from '../../../../components/ui/ConfirmationModal'

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
    const [groupList, setGroupList] = useState<Array<GroupDTO>>([]);
    const [selectedGroup, setActiveGroup] = useState<GroupDTO>();
    const [idForDeletion, setIdForDeletion] = useState<IDType>('');
    const [filter, setFilter] = useState<string>("");
    const {user} = props;

    const matchFilter = (input: string) : boolean => {
      //Very basic search => possibly modify
      return (input.search(filter) >= 0);
    }

    const createNewGroup = () => {
      setOpenModal(true);
      setActiveGroup(undefined);
    }

    const onUpdateClick = (group_id: IDType) => {
      setActiveGroup(groupList.find((item) => item.id === group_id));
      setOpenModal(true);
    }

    const onDeleteClick = (id: IDType) => {
      setIdForDeletion(id);
      setOpenConfirmationModal(true);
    }

    const manageGroupDeletion = async () => {
        try{
          // 1) Call backend (Delete)
          const deletedGroupId = await deleteGroup(idForDeletion as string);
          // 2) Delete group locally from groupList
          setGroupList(groupList.filter((item) => item.id !== deletedGroupId));
          enqueueSnackbar(t('settings:onGroupDeleteSuccess'), { variant: 'success' });
        }
        catch(e)
        {
            enqueueSnackbar(t('settings:onGroupDeleteError'), { variant: 'error' }); 
        }
        setIdForDeletion(-1);
        setOpenConfirmationModal(false);
    }

    const onModalClose = () => {
      setOpenModal(false);
    }

    const onModalSave = async (name: string) => {
      try{
          if(!!selectedGroup)
          {
              const updatedGroup = await updateGroup(selectedGroup.id, name);
              const tmpList = ([] as Array<GroupDTO>).concat(groupList);
              const index = tmpList.findIndex((item) => item.id === selectedGroup.id)
              if(index >= 0)
              {
                tmpList[index].name = updatedGroup.name;
                setGroupList(tmpList);
                enqueueSnackbar(t('settings:onGroupUpdate'), { variant: 'success' });
              }  
          }
          else
          {
              const newGroup = await createGroup(name);
              setGroupList(groupList.concat(newGroup));
              setActiveGroup(newGroup);
              enqueueSnackbar(t('settings:onGroupCreation'), { variant: 'success' });     
          }
      }
      catch(e)
      {
          enqueueSnackbar(t('settings:onGroupSaveError'), { variant: 'error' });
      }
      onModalClose();
  }

    useEffect(() => {
      const init = async () =>{

        try {
          const groups = await getGroups();
          setGroupList(groups.filter((item) => item.id !== "admin"));
        } catch (e) {
          enqueueSnackbar(t('settings:groupsError'), { variant: 'error' });
        }
  
      }
      init();
    }, [user, t, enqueueSnackbar]);

    return (
      <GenericSettingView searchFilter={(input: string) => setFilter(input)}
                          placeholder={t('settings:groupsSearchbarPlaceholder')}
                          buttonValue={t('settings:createGroup')}
                          onButtonClick={createNewGroup}>
                          {
                            groupList.map((item) => 
                             matchFilter(item.name) &&
                             item.id !== 'admin' && 
                                          <ItemSettings key={item.id}
                                            id={item.id}
                                            value={String(item.name)}
                                            onDeleteCLick={onDeleteClick}
                                            onUpdateClick={onUpdateClick} />)
                          }
        {openModal && <GroupModal open={openModal}
                                  onClose={onModalClose}
                                  onSave={onModalSave}
                                  group={selectedGroup}/>}
        {openConfirmationModal && <ConfirmationModal open={openConfirmationModal}
                                                     title={t('main:confirmationModalTitle')}
                                                     message={t('settings:deleteGroupConfirmation')}
                                                     handleYes={manageGroupDeletion}
                                                     handleNo={() => setOpenConfirmationModal(false)}/>}
      </GenericSettingView>
    );

}

export default connector(GroupsSettings)
