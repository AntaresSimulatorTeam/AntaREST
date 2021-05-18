import React, { useState, useEffect } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { AppState } from '../../../reducers';
import GenericSettingView from '../../../../components/Settings/GenericSettingView';
import ItemSettings from '../../../../components/Settings/ItemSettings';
import { getUsers} from '../../../../services/api/user';
import {UserDTO } from '../../../../common/types';
import UserModal from './UserModal'

const mapState = (state: AppState) => ({
    user: state.auth.user,
  });

const connector = connect(mapState);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const UsersSettings = (props: PropTypes) => {

    const [t] = useTranslation();
    const { enqueueSnackbar } = useSnackbar();
    const [userList, setUserList] = useState<UserDTO[]>([]);
    const [filter, setFilter] = useState<string>("");
    const {user} = props;

    // User modal
    const [openModal, setOpenModal] = useState<boolean>(false);
    const [newUser, setNewUser] = useState<boolean>(true);
    const [currentUser, setCurrentUser] = useState<UserDTO|undefined>();

    const createNewUser = () => {
          // 1) We want to create a new user
          setNewUser(true);
          // 2) Open modal
          setOpenModal(true);
    }

    const updateUser = (id: string | number) => {
      // 1) We want to update user
      setNewUser(false);
      // 2) Set current user id
      setCurrentUser(userList.find((item)=> item.id === id));
      // 3) Open modal
      setOpenModal(true);
      // 4) Reload user list ?
  }

    const deleteUser = (id: string | number) => {
      // Implement "are you sure ?" modal. Then =>
      // Call backend for deletion
      // Reload user list ?
    }

    const onModalClose = () => {
      // 1) Close UserModal
      setOpenModal(false);
      // 2) Reload user list ?
    }

    const matchFilter = (input: string) : boolean => {
      //Very basic search => possibly modify
      return (input.search(filter) >= 0);
    }

    useEffect(() => {
      const init = async () =>{

        try {
          const users = await getUsers();
          console.log('USER LIST')
          console.log(users)
          setUserList(users);
  
        } catch (e) {
          enqueueSnackbar(t('settings:usersError'), { variant: 'error' });
        }
  
      }
      init();
    }, [user, t, enqueueSnackbar]);

    return (
      <GenericSettingView searchFilter={(input: string) => setFilter(input)}
                          placeholder={t('settings:usersSearchbarPlaceholder')}
                          buttonValue={t('settings:createUser')}
                          onButtonClick={() => createNewUser()}>
                          {
                            userList.map((item) => 
                            item.name && // To delete
                            matchFilter(item.name) && 
                                          <ItemSettings key={item.id}
                                            id={item.id}
                                            value={String(item.name)}
                                            onDeleteCLick={deleteUser}
                                            onUpdateClick={updateUser} />)
                          }
        {openModal && <UserModal  open={openModal} // Why 'openModal &&' ? => Because otherwise previous data are still present
                                  user={{newUser, userInfos: currentUser}}
                                  onClose={onModalClose} />}
      </GenericSettingView>

    );

}

export default connector(UsersSettings)
