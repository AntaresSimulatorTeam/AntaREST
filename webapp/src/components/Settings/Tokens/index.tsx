import React from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { AppState } from '../../../App/reducers';
import { isUserAdmin } from '../../../services/utils';
import TokenAdmin from './TokenAdmin';
import TokenNormal from './TokenNormal';

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const connector = connect(mapState);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const TokensSettings = (props: PropTypes) => {
  const { user } = props;
  const isAdmin = !!user && isUserAdmin(user);

  if (isAdmin) return <TokenAdmin user={user} />;
  return <TokenNormal user={user} />;
};

export default connector(TokensSettings);
