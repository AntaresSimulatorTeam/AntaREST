import React from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { AppState } from '../reducers';
import { isUserAdmin } from '../../services/utils';
import GenericNavView from '../../components/ui/NavComponents/GenericNavView';
import GroupsSettings from '../../components/Settings/Groups';
import TokensSettings from '../../components/Settings/Tokens';
import UsersSettings from '../../components/Settings/Users';

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const connector = connect(mapState);

type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const UserSettings = (props: PropTypes) => {
  const { user } = props;

  const adminUserData = {
    'settings:users': () => <UsersSettings />,
    'settings:groups': () => <GroupsSettings />,
    'settings:tokens': () => <TokensSettings />,
  };

  const normalUserData = {
    'settings:tokens': () => <TokensSettings />,
  };

  if (user) {
    const isAdmin = isUserAdmin(user);

    return (
      <GenericNavView
        items={isAdmin ? adminUserData : normalUserData}
        initialValue={isAdmin ? 'settings:users' : 'settings:tokens'}
      />
    );
  }
  return null;
};

export default connector(UserSettings);
