import React, { useState, useEffect } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { AppState } from '../../../reducers';
import GenericSettingView from '../../../../components/Settings/GenericSettingView';
import ItemSettings from '../../../../components/Settings/ItemSettings';
import GroupModal from './GroupModal'
import { getGroups} from '../../../../services/api/user';
import {GroupDTO } from '../../../../common/types'

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
    const [isNewGroup, setNewGroup] = useState<boolean>(true);
    const [groupList, setGroupList] = useState<GroupDTO[]>([]);
    const [selectedGroup, setActiveGroup] = useState<GroupDTO>();
    const [filter, setFilter] = useState<string>("");
    const {user} = props;

    const matchFilter = (input: string) : boolean => {
      //Very basic search => possibly modify
      return (input.search(filter) >= 0);
    }

    const createNewGroup = () => {
      setNewGroup(true)
      setOpenModal(true);
      setActiveGroup(undefined);
    }

    const updateGroup = (group_id: string | number) => {
      setNewGroup(false);
      setActiveGroup(groupList.find((item) => item.id === group_id));
      setOpenModal(true);
    }

    const deleteGroup = (id: string | number) => {
      // 1) Call backend (Delete)
      // 2) Delete group locally (from groupList) or reload groupList from Backend ?
    }

    const onModalClose = () => {
      // 1) Close UserModal
      setOpenModal(false);
      // 2) Reload user list ?
    }

    useEffect(() => {
      const init = async () =>{

        try {
          const groups = await getGroups();
          setGroupList(groups);
  
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
                                          <ItemSettings key={item.id}
                                            id={item.id}
                                            value={String(item.name)}
                                            onDeleteCLick={deleteGroup}
                                            onUpdateClick={updateGroup} />)
                          }
        {openModal && <GroupModal open={openModal}
                                  onClose={onModalClose}
                                  group={{isNewGroup, item: selectedGroup}}/>}
      </GenericSettingView>
    );

}

export default connector(GroupsSettings)
