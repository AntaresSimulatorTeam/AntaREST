/* eslint-disable react-hooks/exhaustive-deps */
import React, { PropsWithChildren, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { createStyles, makeStyles, Theme, Typography } from '@material-ui/core';
import { ConnectedProps, connect } from 'react-redux';
import debug from 'debug';
import WarningIcon from '@material-ui/icons/Warning';
import { AppState } from '../reducers';
import { isUserAdmin } from '../../services/utils';
import { getMaintenanceMode } from '../../services/api/maintenance';
import { getConfig } from '../../services/config';
import { setMaintenanceMode } from '../../ducks/global';
import SmokeEffect from './SmokeEffect';

const logError = debug('antares:maintenancewrapper:error');

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      display: 'flex',
      height: '100%',
      width: '100%',
      flexFlow: 'column nowrap',
      justifyContent: 'center',
      alignItems: 'center',
      background: `linear-gradient(${theme.palette.secondary.main}, ${theme.palette.primary.main})`,
    },
    message: {
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 999,
    },
    icon: {
      color: theme.palette.secondary.main,
      width: '200px',
      height: '200px',
      animation: '$myEffect 500ms linear 0s infinite alternate',
      marginRight: theme.spacing(4),
    },
    '@keyframes myEffect': {
      '0%': {
        transform: 'scale(1.0)',
      },
      '100%': {
        transform: 'scale(1.1)',
      },
    },
    text: {
      fontSize: '4em',
      color: 'white',
      fontWeight: 'bold',
      //animation: '$myEffect 2s linear 0s infinite alternate',
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
  const { children, user, maintenance, setMaintenance } = props;

  useEffect(() => {
    const init = async () => {
      const { maintenanceMode } = getConfig();
      try {
        const tmpMaintenance = await getMaintenanceMode();
        setMaintenance(tmpMaintenance);
      } catch (e) {
        logError(e);
        setMaintenance(maintenanceMode);
      }
    };
    init();
  }, []);

  if (maintenance && (user !== undefined && !isUserAdmin(user))) {
    return (
      <div className={classes.root}>
        <SmokeEffect />
        <div className={classes.message}>
          <WarningIcon className={classes.icon} />
          <Typography className={classes.text}>Oups ! App under maintenance.</Typography>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default connector(MaintenanceWrapper);
