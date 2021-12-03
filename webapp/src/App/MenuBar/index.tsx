import React from 'react';
import { ConnectedProps, connect } from 'react-redux';
import { AppBar, Toolbar, Typography, createStyles, makeStyles, Theme, Tooltip } from '@material-ui/core';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import PortableWifiOffIcon from '@material-ui/icons/PortableWifiOff';
import { useTranslation } from 'react-i18next';
import clsx from 'clsx';
import logo from './logo.png';
import UserBadge from '../../components/UserBadge';
import { getConfig } from '../../services/config';
import { AppState } from '../reducers';
import './style.css';
import DownloadBadge from '../../components/DownloadsListing/DownloadBadge';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    menuitem: {
      marginLeft: theme.spacing(2),
      '&:hover': {
        textDecoration: 'underline',
      },
    },
    altmenuitem: {
      marginRight: theme.spacing(2),
    },
    logo: {
      marginRight: theme.spacing(2),
      height: '32px',
    },
    mainmenu: {
      flexGrow: 1,
      display: 'flex',
      alignItems: 'center',
    },
    title: {
      fontSize: 'x-large',
      fontWeight: 'bold',
    },
    version: {
      fontSize: 'small',
      color: theme.palette.primary.light,
      marginLeft: theme.spacing(0.5),
      marginBottom: '-10px',
      marginRight: theme.spacing(1.5),
    },
  }));

const mapState = (state: AppState) => ({
  websocketConnected: state.websockets.connected,
});

const mapDispatch = ({});

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
type PropTypes = PropsFromRedux;

const MenuBar = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { websocketConnected } = props;
  const versionInfo = getConfig().version;

  return (
    <AppBar position="static">
      <Toolbar variant="dense">
        <div className={classes.mainmenu}>
          <div className={classes.title}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <img src={logo} alt="logo" className={classes.logo} />
              <Link to="/">AntaREST</Link>
              <Tooltip title={versionInfo.gitcommit}>
                <div className={classes.version}>
                  {versionInfo.version}
                </div>
              </Tooltip>
            </div>
          </div>
          <Typography className={classes.menuitem}>
            <Link to="/">{t('main:studies')}</Link>
          </Typography>
          <Typography className={classes.menuitem}>
            <Link to="/jobs">{t('main:jobs')}</Link>
          </Typography>
          <Typography className={classes.menuitem}>
            <Link to="/data">{t('main:data')}</Link>
          </Typography>
          <DownloadBadge>
            <Typography className={classes.menuitem}>
              <Link to="/downloads">{t('main:exports')}</Link>
            </Typography>
          </DownloadBadge>
        </div>
        {!websocketConnected &&
          (
            <Tooltip title={t('main:websocketstatusmessage') as string}>
              <PortableWifiOffIcon className={clsx(classes.altmenuitem, 'pulsing-opacity')} />
            </Tooltip>
          )}
        <Typography className={classes.altmenuitem}>
          <Link to="/swagger">API</Link>
        </Typography>
        <Typography className={classes.altmenuitem}>
          <a
            href="https://antares-web.readthedocs.io/en/latest"
            target="_blank"
            rel="noopener noreferrer"
          >
            Docs
          </a>
        </Typography>
        <div className={classes.altmenuitem}>
          <a
            href="https://github.com/AntaresSimulatorTeam/AntaREST"
            target="_blank"
            rel="noopener noreferrer"
          >
            <FontAwesomeIcon size="2x" icon={['fab', 'github']} />
          </a>
        </div>
        <div className={classes.altmenuitem}>
          <UserBadge />
        </div>
      </Toolbar>
    </AppBar>
  );
};

export default connector(MenuBar);
