import React from 'react';
import { AppBar, Toolbar, Typography, createStyles, makeStyles, Theme } from '@material-ui/core';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { useTranslation } from 'react-i18next';
import logo from './logo.png';
import UserBadge from '../../components/UserBadge';

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
  }));

const MenuBar = () => {
  const classes = useStyles();
  const [t] = useTranslation();

  return (
    <AppBar position="static">
      <Toolbar variant="dense">
        <div className={classes.mainmenu}>
          <div className={classes.title}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <img src={logo} alt="logo" className={classes.logo} />
              <Link to="/">AntaREST</Link>
            </div>
          </div>
          <Typography className={classes.menuitem}>
            <Link to="/">{t('main:studies')}</Link>
          </Typography>
          <Typography className={classes.menuitem}>
            <Link to="/jobs">{t('main:jobs')}</Link>
          </Typography>
        </div>
        <Typography className={classes.altmenuitem}>
          <Link to="/swagger">API</Link>
        </Typography>
        <Typography className={classes.altmenuitem}>
          <a href="https://api-antares.readthedocs.io/en/dev/inside.html" target="_blank" rel="noopener noreferrer">Docs</a>
        </Typography>
        <div className={classes.altmenuitem}>
          <a href="https://github.com/AntaresSimulatorTeam/AntaREST" target="_blank" rel="noopener noreferrer">
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

export default MenuBar;
