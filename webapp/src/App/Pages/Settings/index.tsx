import React, {useState, useEffect} from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useTranslation } from 'react-i18next';
import { AppState } from '../../reducers';
import {isUserAdmin} from '../../../services/utils'
import GenericSettings from '../../../components/Settings/GenericSettings'
import GroupsSettings from './Groups';
import TokensSettings from './Tokens';
import UsersSettings from './Users';

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const connector = connect(mapState);

type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const UserSettings = (props: PropTypes) => {

  const { user} = props;
  console.log(user);

  const [isAdmin, setAdminStatus] = useState<boolean>(false);
  
  const [t] = useTranslation();

  useEffect(() => {

    // Is admin ?
    if(!!user && isUserAdmin(user))
      setAdminStatus(true);
    else
      setAdminStatus(false);
  
  }, [user])

  const adminUserData = {
    [t('settings:users')]: () => <UsersSettings />,
    [t('settings:groups')]: () => <GroupsSettings />,
    [t('settings:tokens')]: () => <TokensSettings />,
  }

  const normalUserData = {
    [t('settings:tokens')]: () => <TokensSettings />,
  }

  // Why !!user ? => Error otherwise (NavState)
  return !!user ? (<GenericSettings items={isAdmin ? adminUserData : normalUserData} />) : null;
};

export default connector(UserSettings);