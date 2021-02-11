import React from 'react';
import { AppBar, Toolbar, Typography, createStyles, makeStyles, Theme } from '@material-ui/core';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import logo from './logo.png';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    menuitem: {
      marginRight: theme.spacing(2),
    },
    logo: {
      marginRight: theme.spacing(2),
      height: '32px',
    },
    title: {
      flexGrow: 1,
      fontSize: 'x-large',
      fontWeight: 'bold',
    },
  }));

const MenuBar = () => {
  const classes = useStyles();

  return (
    <AppBar position="static">
      <Toolbar variant="dense">
        <div className={classes.title}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <img src={logo} alt="logo" className={classes.logo} />
            <Link to="/">AntaREST</Link>
          </div>
        </div>
        <Typography className={classes.menuitem}>
          <Link to="/swagger">API</Link>
        </Typography>
        <Typography className={classes.menuitem}>
          <a href="https://api-antares.readthedocs.io/en/dev/inside.html" target="_blank" rel="noopener noreferrer">Docs</a>
        </Typography>
        <div className={classes.menuitem}>
          <a href="https://github.com/AntaresSimulatorTeam/AntaREST" target="_blank" rel="noopener noreferrer">
            <FontAwesomeIcon size="2x" icon={['fab', 'github']} />
          </a>
        </div>
      </Toolbar>
    </AppBar>
  );
};

export default MenuBar;
