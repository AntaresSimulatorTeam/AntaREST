import React, { useState, useEffect } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { AppState } from '../../reducers';
import GenericSettingView from '../../../components/Settings/GenericSettingView';
import ItemSettings from '../../../components/Settings/ItemSettings';
import { getUsers} from '../../../services/api/user';
import {UserDTO } from '../../../common/types';

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
                          onButtonClick={() => console.log("Button")}>
                          {
                            userList.map((item) => 
                            item.name && // To delete
                            matchFilter(item.name) && 
                                          <ItemSettings key={item.id}
                                            id={item.id}
                                            value={String(item.name)}
                                            onDeleteCLick={(id: number) => console.log("Delete "+id)}
                                            onUpdateClick={(id : number) => console.log("Update "+id)} />)
                          }
      </GenericSettingView>
    );

}

export default connector(UsersSettings)
