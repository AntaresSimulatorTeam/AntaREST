import React from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { AppState } from '../reducers';
import { isGroupAdmin, isUserAdmin } from '../../services/utils';
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

interface GenericNavData {
  data: {
    [item: string]: () => JSX.Element;
};
initialValue: string;
}

const UserSettings = (props: PropTypes) => {
  const { user } = props;

  const getGenericNavData = (): GenericNavData => {
    if (user !== undefined) {
      if (isUserAdmin(user)) {
        return {
          data: {
            'settings:users': () => <UsersSettings />,
            'settings:groups': () => <GroupsSettings />,
            'settings:tokens': () => <TokensSettings />,
          },
          initialValue: 'settings:users',
        };
      }

      if (isGroupAdmin(user)) {
        return {
          data: {
            'settings:groups': () => <GroupsSettings />,
            'settings:tokens': () => <TokensSettings />,
          },
          initialValue: 'settings:groups',
        };
      }

      return {
        data: {
          'settings:tokens': () => <TokensSettings />,
        },
        initialValue: 'settings:tokens',
      };
    }
    return { data: {}, initialValue: '' };
  };

  if (user) {
    const data = getGenericNavData();

    return (
      <GenericNavView
        items={data.data}
        initialValue={data.initialValue}
      />
    );
  }
  return null;
};

export default connector(UserSettings);
