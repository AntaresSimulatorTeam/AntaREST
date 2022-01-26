import React, { useEffect } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useHistory } from 'react-router-dom';
import { logoutAction } from '../../ducks/auth';
import { isUserAdmin } from '../../services/utils';
import { AppState } from '../reducers';

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const mapDispatch = ({
  logout: logoutAction,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const Logout = (props: PropTypes) => {
  const { user, logout } = props;
  const history = useHistory();

  useEffect(() => {
    if (user) {
      if (!isUserAdmin(user)) logout();
      history.push('/');
    }
  }, [history, logout, user]);

  return <div />;
};

export default connector(Logout);
