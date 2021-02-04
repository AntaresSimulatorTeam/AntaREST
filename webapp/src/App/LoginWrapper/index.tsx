import React, { PropsWithChildren } from 'react';
import Particles from 'react-particles-js';
import { useTranslation } from 'react-i18next';
import { createStyles, makeStyles, Theme, Typography, TextField, Button } from '@material-ui/core';
import { ConnectedProps, connect } from 'react-redux';
import { useForm } from 'react-hook-form';
import { AppState } from '../reducers';
import { loginUser } from '../../ducks/auth';
import particlesConf from './particles.json';
import logo from './antarestlogo.png';
import './particles.css';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      display: 'flex',
      height: '100%',
    },
    sidebar: {
      flex: '40% 0 0',
      backgroundColor: theme.palette.primary.dark,
    },
    main: {
      flexGrow: 1,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    },
    loginFormContainer: {
      width: '70%',
    },
    form: {
      marginTop: theme.spacing(2),
    },
    submitButton: {
      display: 'flex',
      justifyContent: 'center',
      marginTop: theme.spacing(6),
    },
  }));

interface Inputs {
  username: string;
  password: string;
}

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const mapDispatch = ({
  login: loginUser,
});

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
type PropTypes = PropsFromRedux;

const LoginWrapper = (props: PropsWithChildren<PropTypes>) => {
  const classes = useStyles();
  const { register, handleSubmit } = useForm<Inputs>();
  const [t] = useTranslation();
  const { children } = props;
  const { user, login } = props;

  const onSubmit = (data: Inputs) => {
    login({ user: data.username, token: 'todo' });
  };

  if (!user) {
    return (
      <div className={classes.root}>
        <div className={classes.sidebar}>
          <div style={{ height: '100%', position: 'relative' }}>
            <Particles
              params={particlesConf}
            />
            <div style={{ zIndex: 50, position: 'absolute', top: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%' }}>
              <img style={{ backgroundColor: '#fff' }} height="140px" src={logo} alt="logo" />
            </div>

          </div>
        </div>
        <div className={classes.main}>
          <div>
            <Typography variant="h2" component="h1">Antares Web</Typography>
            <div className={classes.loginFormContainer}>
              <form className={classes.form} onSubmit={handleSubmit(onSubmit)}>
                <TextField
                  required
                  id="login"
                  label="NNI"
                  fullWidth
                  inputProps={{ name: 'username', ref: register({ required: true }) }}
                />
                <TextField
                  id="password"
                  label={t('main:password')}
                  required
                  fullWidth
                  type="password"
                  inputProps={{ name: 'password', ref: register({ required: true }) }}
                />
                <div className={classes.submitButton}>
                  <Button type="submit" variant="contained" color="primary">
                    {t('main:connexion')}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default connector(LoginWrapper);
