/* eslint-disable react-hooks/exhaustive-deps */
import React, { PropsWithChildren, useState, useEffect } from 'react';
import Particles from 'react-particles-js';
import { useTranslation } from 'react-i18next';
import CircularProgress from '@material-ui/core/CircularProgress';
import { createStyles, makeStyles, Theme, Typography, TextField, Button } from '@material-ui/core';
import { ConnectedProps, connect } from 'react-redux';
import { useForm } from 'react-hook-form';
import debug from 'debug';
import { AppState } from '../reducers';
import { loginUser, logoutAction } from '../../ducks/auth';
import { login as loginRequest, needAuth, refresh } from '../../services/api/auth';
import particlesConf from './particles.json';
import logo from './antarestlogo.png';
import './particles.css';
import GlobalPageLoadingError from '../../components/ui/GlobalPageLoadingError';
import AppLoader from '../../components/ui/loaders/AppLoader';
import { updateRefreshInterceptor } from '../../services/api/client';
import { UserInfo } from '../../common/types';

const logError = debug('antares:loginwrapper:error');

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
    errorMessage: {
      marginTop: theme.spacing(2),
      color: theme.palette.error.main,
      marginBottom: -theme.spacing(4),
      fontSize: '0.9rem',
    },
  }));

type FormStatus = 'loading' | 'default' | 'success';

interface Inputs {
  username: string;
  password: string;
}

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const mapDispatch = ({
  login: loginUser,
  logout: logoutAction,
});

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
type PropTypes = PropsFromRedux;

const LoginWrapper = (props: PropsWithChildren<PropTypes>) => {
  const classes = useStyles();
  const { register, handleSubmit, reset } = useForm<Inputs>();
  const [status, setStatus] = useState<FormStatus>('default');
  const [authRequired, setAuthRequired] = useState<boolean>();
  const [connexionError, setConnexionError] = useState(false);
  const [loginError, setLoginError] = useState<string>();
  const [t] = useTranslation();
  const { children } = props;
  const { user, login, logout } = props;

  const onSubmit = async (data: Inputs) => {
    setStatus('loading');
    setLoginError('');
    setTimeout(async () => {
      try {
        const res = await loginRequest(data.username, data.password);
        setStatus('success');
        login(res);
      } catch (e) {
        setStatus('default');
        setLoginError(e.data?.message || t('main:loginError'));
      } finally {
        reset({ username: data.username });
      }
    }, 500);
  };

  useEffect(() => {
    (async () => {
      try {
        if (user) {
          updateRefreshInterceptor(async (): Promise<UserInfo|undefined> => {
            try {
              return refresh(user, login, logout);
            } catch (e) {
              logError('Failed to refresh token');
            }
            return undefined;
          });
        }
        const res = await needAuth();
        setAuthRequired(res);
      } catch (e) {
        setConnexionError(true);
      }
    })();
  }, []);

  useEffect(() => {
    if (user) {
      updateRefreshInterceptor(async (): Promise<UserInfo|undefined> => {
        try {
          return refresh(user, login, logout);
        } catch (e) {
          logError('Failed to refresh token');
        }
        return undefined;
      });
    }
  }, [user]);

  if (authRequired === undefined) {
    return <AppLoader />;
  }

  if (connexionError) {
    return <GlobalPageLoadingError />;
  }

  if (!authRequired || user) {
    return <>{children}</>;
  }

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
              {loginError && (
                <div className={classes.errorMessage}>{loginError}</div>
              )}
              <div className={classes.submitButton}>
                <Button disabled={status === 'loading'} type="submit" variant="contained" color="primary">
                  {status === 'loading' && <CircularProgress size="1em" style={{ marginRight: '1em' }} />}
                  {t('main:connexion')}
                </Button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default connector(LoginWrapper);
