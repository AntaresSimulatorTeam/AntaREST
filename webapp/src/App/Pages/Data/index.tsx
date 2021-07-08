import React from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { AppState } from '../../reducers';
import GenericNavView from '../../../components/ui/NavComponents/GenericNavView';
import DataPage from './DataPage';

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const connector = connect(mapState);

type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const DataManagement = (props: PropTypes) => {
  const { user } = props;

  const mainTab = {
    'data:data': () => <DataPage />,
  };

  if (user) {
    return (
      <GenericNavView
        items={mainTab}
        initialValue="data:data"
      />
    );
  }
  return null;
};

export default connector(DataManagement);
