/* eslint-disable react-hooks/exhaustive-deps */
import React, { PropsWithChildren, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { createStyles, makeStyles, Theme, Typography } from '@material-ui/core';
import { ConnectedProps, connect } from 'react-redux';
import debug from 'debug';
import ErrorIcon from '@material-ui/icons/Error';
import { AppState } from '../reducers';
import { isUserAdmin } from '../../services/utils';
import { getMaintenanceMode } from '../../services/api/maintenance';
import { getConfig } from '../../services/config';
import { setMaintenanceMode } from '../../ducks/global';
import MessageInfoModal from './MessageInfoModal';
import Stars from './Stars';

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
      backgroundColor: theme.palette.primary.main,
    },
    message: {
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 999,
    },
    icon: {
      color: 'white',
      width: '160px',
      height: '160px',
      animation: '$myEffect 2s linear 0s infinite alternate',
      marginRight: theme.spacing(5),
    },
    '@keyframes myEffect': {
      '0%': {
        transform: 'scale(1.0)',
      },
      '100%': {
        transform: 'scale(1.05)',
      },
    },
    text: {
      fontSize: '3.5em',
      color: 'white',
      fontWeight: 'bold',
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
        <Stars />
        <div className={classes.message}>
          <ErrorIcon className={classes.icon} />
          <Typography className={classes.text}>
            {t('main:appUnderMaintenance')}
            <br />
            {t('main:comeBackLater')}
          </Typography>
        </div>
        <MessageInfoModal />
      </div>
    );
  }

  return (
    <>
      {children}
    </>
  );
};

export default connector(MaintenanceWrapper);
