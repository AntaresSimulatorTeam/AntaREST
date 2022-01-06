/* eslint-disable react-hooks/exhaustive-deps */
import React, { PropsWithChildren, useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { createStyles, makeStyles, Theme } from '@material-ui/core';
import { ConnectedProps, connect } from 'react-redux';
import debug from 'debug';
import { AppState } from '../reducers';
import { MaintenanceMode } from '../../common/types';
import { setMaintenanceMode } from '../../ducks/global';
import { isUserAdmin } from '../../services/utils';
import { getMaintenanceMode } from '../../services/api/maintenance';

const logError = debug('antares:loginwrapper:error');

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      display: 'flex',
      height: '100%',
      width: '100%',
      backgroundColor: 'black',
    },
  }));

const mapState = (state: AppState) => ({
  user: state.auth.user,
  maintenance: state.global.maintenanceMode,
});

const mapDispatch = ({
  setMaintenance: setMaintenanceMode,
});

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
type PropTypes = PropsFromRedux;

const MaintenanceWrapper = (props: PropsWithChildren<PropTypes>) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { children } = props;
  const { user, maintenance, setMaintenance } = props;

  useEffect(() => {
    const init = async () => {
      try {
        const tmpMaintenance = await getMaintenanceMode();
        setMaintenance(tmpMaintenance);
      } catch (e) {
        console.log(e);
      }
    };
    init();
  }, []);

  if (maintenance.mode === MaintenanceMode.MAINTENANCE_MODE && (user !== undefined && !isUserAdmin(user))) {
    return (
      <div className={classes.root} />
    );
  }

  return <>{children}</>;
};

export default connector(MaintenanceWrapper);
