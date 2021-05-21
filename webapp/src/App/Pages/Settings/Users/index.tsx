import React, { useState, useEffect } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { AppState } from '../../../reducers';
import GenericSettingView from '../../../../components/Settings/GenericSettingView';
import ItemSettings from '../../../../components/Settings/ItemSettings';
import { getUsers, deleteUser} from '../../../../services/api/user';
import {UserDTO, IDType } from '../../../../common/types';
import UserModal from './UserModal'
import ConfirmationModal from '../../../../components/ui/ConfirmationModal'

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
    const [idForDeletion, setIdForDeletion] = useState<IDType>(-1);
    const [filter, setFilter] = useState<string>("");
    const {user} = props;

    // User modal
    const [openModal, setOpenModal] = useState<boolean>(false);
    const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);
    const [currentUser, setCurrentUser] = useState<UserDTO|undefined>();

    const createNewUser = () => {
          setCurrentUser(undefined);
          setOpenModal(true);
    }

    const onUpdateClick = (id: IDType) : void => {
      setCurrentUser(userList.find((item)=> item.id === id));
      setOpenModal(true);
  }

  const onDeleteClick = (id: IDType) => {
    setIdForDeletion(id);
    setOpenConfirmationModal(true);
  }

  const manageUserDeletion = async () => {
      // Implement "are you sure ?" modal. Then =>
      try
      {
        const res = await deleteUser(idForDeletion as number);
        setUserList(userList.filter((item) => item.id !== idForDeletion));
        console.log(res);
        enqueueSnackbar(t('settings:onUserDeleteSuccess'), { variant: 'success' });
      }
      catch(e)
      {
        enqueueSnackbar(t('settings:onUserDeleteError'), { variant: 'error' });
      }
      setIdForDeletion(-1);
      setOpenConfirmationModal(false);
  }

    const onModalClose = () => {
      setOpenModal(false);
    }

    const onNewUserCreaion = (newUser : UserDTO) : void => {
      setUserList(userList.concat(newUser));
      setCurrentUser(newUser);
    }

    const matchFilter = (input: string) : boolean => {
      //Very basic search => possibly modify
      return (input.search(filter) >= 0);
    }

    useEffect(() => {
      const init = async () =>{

        try {
          const users = await getUsers();
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
                            item.name !== 'admin' && 
                            matchFilter(item.name) && 
                                          <ItemSettings key={item.id}
                                            id={item.id}
                                            value={String(item.name)}
                                            onDeleteCLick={onDeleteClick}
                                            onUpdateClick={onUpdateClick} />)
                          }
        {openModal && <UserModal  open={openModal} // Why 'openModal &&' ? => Because otherwise previous data are still present
                                  userInfos={currentUser}
                                  onNewUserCreaion={onNewUserCreaion}
                                  onClose={onModalClose} />}
        {openConfirmationModal && <ConfirmationModal open={openConfirmationModal}
                                                     title={t('main:confirmationModalTitle')}
                                                     message={t('settings:deleteUserConfirmation')}
                                                     handleYes={manageUserDeletion}
                                                     handleNo={() => setOpenConfirmationModal(false)}/>}
      </GenericSettingView>

    );

}

export default connector(UsersSettings)
